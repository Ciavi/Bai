import asyncio

import requests
from discord import app_commands, Interaction, Member
from discord.ext import commands
from sentence_transformers import SentenceTransformer, util

from commands.messages import embed_api_error, embed_permissions_error, embed_configuration_error, message_imprisonment, \
    message_wrong, message_right, message_switch_sudoku
from commands.utils import is_guild_configured, is_user_warden, is_user_imprisoned, is_valid_user_solution
from data.interface import create_riddle, delete_riddle, read_riddle, update_riddle


class Jail(commands.Cog):
    group = app_commands.Group(name="jail", description="Jail commands")

    def __init__(self, bot):
        self.bot = bot
        self.model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")


    @group.command(name="imprison", description="Punish naughty people")
    @app_commands.describe(member="The naughty member to punish")
    async def imprison(self, interaction: Interaction, member: Member):
        guild, is_configured = await is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_warden(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        if member.id == self.bot.user.id:
            await interaction.response.send_message("Naughty naughty! Can't jail ol' Bai!", ephemeral=True)
            return

        if member.bot:
            await interaction.response.send_message("Why would you jail the innocent?", ephemeral=True)
            return

        if is_user_imprisoned(guild, member):
            await interaction.response.send_message("User is already in jail!", ephemeral=True)
            return

        response = requests.get("https://riddles-api.vercel.app/random")

        if response.status_code != 200:
            await interaction.response.send_message(embed=embed_api_error(response), ephemeral=True)
            return

        await member.add_roles(interaction.guild.get_role(guild.configuration['inmate_role']))

        await interaction.response.send_message("User is now in jail!", ephemeral=True)

        riddle_json = response.json()

        channel = interaction.guild.get_channel(guild.configuration['jail_channel'])
        riddle = create_riddle(guild.id, member.id, riddle_json["riddle"], riddle_json["answer"])
        await channel.send(message_imprisonment(riddle, member))


    @group.command(name="release", description="Release them naughties")
    @app_commands.describe(inmate="The inmate to release")
    async def release(self, interaction: Interaction, inmate: Member):
        guild, is_configured = await is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_warden(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        if not is_user_imprisoned(guild, inmate):
            await interaction.response.send_message("User is not in jail!", ephemeral=True)
            return

        await inmate.remove_roles(interaction.guild.get_role(guild.configuration['inmate_role']))
        delete_riddle(interaction.guild.id, inmate.id)

        await interaction.response.send_message("User is now out of jail!", ephemeral=True)


    @app_commands.command(name="solve", description="Solve the riddle")
    @app_commands.describe(answer="The answer")
    async def solve(self, interaction: Interaction, answer: str):
        guild, is_configured = await is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        riddle = read_riddle(interaction.guild.id, interaction.user.id)

        if not is_user_imprisoned(guild, interaction.user) and riddle is None:
            await interaction.response.send_message("You don't have a riddle to solve!", ephemeral=True)
            return

        embedding_solution = self.model.encode(riddle.solution, convert_to_tensor=True)
        embedding_answer = self.model.encode(answer, convert_to_tensor=True)
        similarity = util.pytorch_cos_sim(embedding_solution, embedding_answer)

        if not riddle.is_sudoku and similarity.item() < 0.75:
            await interaction.response.send_message(message_wrong(riddle))
            return

        is_user_solution = False

        if riddle.is_sudoku and similarity.item() < 1.00:
            grid_array = [list(map(int, riddle.text[i:i + 9])) for i in range(0, len(riddle.text), 9)]
            answer_array = [list(map(int, answer[i:i + 9])) for i in range(0, len(answer), 9)]

            if not is_valid_user_solution(grid_array, answer_array):
                await interaction.response.send_message(message_wrong(riddle))
                return

            is_user_solution = True

        await interaction.response.send_message(message_right(riddle, is_user_solution))
        await asyncio.sleep(10)

        delete_riddle(interaction.guild.id, interaction.user.id)
        await interaction.user.remove_roles(interaction.guild.get_role(guild.configuration['inmate_role']))


    @app_commands.command(name="sudoku", description="Change riddle into a sudoku if your skill issue is too much to handle")
    async def sudoku(self, interaction: Interaction):
        guild, is_configured = await is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        riddle = read_riddle(interaction.guild.id, interaction.user.id)

        if not is_user_imprisoned(guild, interaction.user) and riddle is None:
            await interaction.response.send_message("You don't have a riddle to solve!", ephemeral=True)
            return

        if riddle.is_sudoku:
            await interaction.response.send_message("You already switched to a sudoku!", ephemeral=True)
            return

        response = requests.get(
            "https://sudoku-api.vercel.app/api/dosuku?query={newboard(limit:1){grids{value,solution,difficulty}}}")

        if response.status_code != 200:
            await interaction.response.send_message(embed=embed_api_error(response), ephemeral=True)
            return

        sudoku_json = response.json()
        sudoku_grid = sudoku_json["newboard"]["grids"][0]["value"]
        sudoku_solution = sudoku_json["newboard"]["grids"][0]["solution"]
        sudoku_difficulty = sudoku_json["newboard"]["grids"][0]["difficulty"]

        sudoku_grid_string = ''.join(str(num) for row in sudoku_grid for num in row)
        sudoku_solution_string = ''.join(str(num) for row in sudoku_solution for num in row)

        riddle = update_riddle(interaction.guild.id, interaction.user.id, sudoku_grid_string,
                               sudoku_solution_string, True)

        await interaction.response.send_message("Heh. Good luck!", ephemeral=True)

        channel = interaction.guild.get_channel(guild.configuration['jail_channel'])
        await channel.send(message_switch_sudoku(riddle, interaction.user, sudoku_difficulty))
