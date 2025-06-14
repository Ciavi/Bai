import asyncio
import enum

import discord
import logging
import requests

from discord import app_commands, Member, Embed, Color, Interaction, Role, User
from requests import Response

from sentence_transformers import SentenceTransformer, util

import system.configuration
import system.historian

from os import environ as env
from discord.ext import commands
from dotenv import load_dotenv

from data.interface import initialise, create_guild, update_guild, create_riddle, read_riddle, delete_riddle, \
    update_riddle
from data.models import Riddle, Guild

load_dotenv()

model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True

configuration = system.configuration.Configuration('conf.json')
logger = system.historian.Logging(configuration)

bot = commands.Bot(command_prefix='^', intents=intents)

async def setup_hook():
    await bot.tree.sync()

bot.setup_hook = setup_hook

def is_guild_configured(guild_id: int):
    guild = create_guild(guild_id)
    return guild, guild.moderator_role is not None and guild.inmate_role is not None and guild.jail_channel is not None


def embed_configuration_error(guild: Guild):
    embed = Embed(color=Color.red(), title=f"Guild `{guild.id}` is not configured correctly!")
    embed.description = (f"All the following variables must be set:\n"
                         f"`moderator_role`: `<@&{guild.moderator_role}>`\n"
                         f"`inmate_role`: `<@&{guild.inmate_role}>`\n"
                         f"`jail_channel`: `<#{guild.jail_channel}>`\n")
    return embed


def is_user_moderator(guild: Guild, member: Member):
    return any(role.id == guild.moderator_role for role in member.roles)


def embed_permissions_error(guild: Guild):
    embed = Embed(color=Color.red(), title=f"You don't have permission to use this command!")
    embed.description = (f"You need the role <@{guild.moderator_role}> to use this command.")
    return embed


def is_user_imprisoned(guild: Guild, member: Member):
    return any(role.id == guild.inmate_role for role in member.roles)


def imprisonment_message(riddle: Riddle, member: Member):
    return (f"## Welcome to the Dungeon <@!{member.id}> 😏\n"
            f"### Solve the following riddle to get out.\n"
            f"-# Use `/solve <answer>` to solve.\n"
            f"-# Use `/sudoku` to switch to a sudoku if your brain is melting.\n"
            f"> {riddle.text}")


def embed_api_error(response: Response):
    embed = Embed(color=Color.red(), title=f"API Error ({response.status_code})")
    embed.description = (f"```\n{response.text}```")
    return embed


def wrong_message(riddle: Riddle):
    if riddle.is_sudoku:
        sudoku_array = [list(map(int, riddle.text[i:i + 9])) for i in range(0, len(riddle.text), 9)]
        sudoku_pretty = display_sudoku(sudoku_array)
        return (f"Wrong! Try again!\n"
                f"```{sudoku_pretty}```")

    return(f"Wrong! Try again!\n"
           f"> {riddle.text}")


def right_message(riddle: Riddle):
    if riddle.is_sudoku:
        solution_array = [list(map(int, riddle.solution[i:i + 9])) for i in range(0, len(riddle.solution), 9)]
        solution_pretty = display_sudoku(solution_array)

        return (f"Good job! The solution was\n"
                f"```{solution_pretty}```\n"
                f"You have regained your freedom. You'll be freed in 10 seconds.")

    return(f"Good job! The answer was `{riddle.solution}`.\n"
           f"You have regained your freedom. You'll be freed in 10 seconds.")


def display_sudoku(grid):
    lines = []
    for i, row in enumerate(grid):
        # Format each row with spaces and vertical dividers
        line = ' '.join(
            str(num) if num != 0 else '.' for num in row[:3]
        ) + " | " + ' '.join(
            str(num) if num != 0 else '.' for num in row[3:6]
        ) + " | " + ' '.join(
            str(num) if num != 0 else '.' for num in row[6:]
        )
        lines.append(line)
        # Add horizontal dividers
        if i in [2, 5]:
            lines.append("-" * 21)
    return '\n'.join(lines)


def switch_sudoku_message(riddle: Riddle, member: Member, difficulty: str):
    grid_array = [list(map(int, riddle.text[i:i+9])) for i in range(0, len(riddle.text), 9)]
    grid_pretty = display_sudoku(grid_array)

    return (f"## Damn <@!{member.id}>, you picked the sudoku instead!\n"
                f"-# Use `/solve <answer>` to solve.\n"
                f"-# The solution is to be given in a string format, ***row-by-row***.\n"
                f"```{grid_pretty}```\n"
                f"Difficulty: `{difficulty}`")

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}#{bot.user.discriminator}')
    initialise()


@bot.tree.command(name="jail", description="Punish naughty people")
@app_commands.describe(member="The member to punish")
async def jail(interaction: Interaction, member: Member):
    guild, is_configured = is_guild_configured(interaction.guild.id)

    if not is_configured:
        await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
        return

    if not is_user_moderator(guild, interaction.user):
        await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
        return

    if member.id == bot.user.id:
        await interaction.response.send_message("Naughty naughty! Can't jail ol' Bai!", ephemeral=True)
        return

    if is_user_imprisoned(guild, member):
        await interaction.response.send_message("User is already in jail!", ephemeral=True)
        return

    response = requests.get("https://riddles-api.vercel.app/random")

    if response.status_code != 200:
        await interaction.response.send_message(embed=embed_api_error(response), ephemeral=True)
        return

    await member.add_roles(interaction.guild.get_role(guild.inmate_role))

    await interaction.response.send_message("User is now in jail!", ephemeral=True)

    riddle_json = response.json()

    channel = interaction.guild.get_channel(guild.jail_channel)
    riddle = create_riddle(guild.id, member.id, riddle_json["riddle"], riddle_json["answer"])
    await channel.send(imprisonment_message(riddle, member))


@bot.tree.command(name="solve", description="Solve the riddle")
@app_commands.describe(answer="The answer")
async def solve(interaction: Interaction, answer: str):
    guild, is_configured = is_guild_configured(interaction.guild.id)
    if not is_configured:
        await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
        return

    riddle = read_riddle(interaction.guild.id, interaction.user.id)

    if not is_user_imprisoned(guild, interaction.user) and riddle is None:
        await interaction.response.send_message("You don't have a riddle to solve!", ephemeral=True)
        return

    embedding_solution = model.encode(riddle.solution, convert_to_tensor=True)
    embedding_answer = model.encode(answer, convert_to_tensor=True)
    similarity = util.pytorch_cos_sim(embedding_solution, embedding_answer)

    if (not riddle.is_sudoku and similarity.item() < 0.75) or (riddle.is_sudoku and similarity.item() < 1.00):
        await interaction.response.send_message(wrong_message(riddle))
        return

    await interaction.response.send_message(right_message(riddle))
    await asyncio.sleep(10)

    delete_riddle(interaction.guild.id, interaction.user.id)
    await interaction.user.remove_roles(interaction.guild.get_role(guild.inmate_role))


@bot.tree.command(name="sudoku", description="Change riddle into a sudoku if your skill issue is too much to handle")
async def sudoku(interaction: Interaction):
    guild, is_configured = is_guild_configured(interaction.guild.id)
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

    response = requests.get("https://sudoku-api.vercel.app/api/dosuku?query={newboard(limit:1){grids{value,solution,difficulty}}}")

    if response.status_code != 200:
        await interaction.response.send_message(embed=embed_api_error(response), ephemeral=True)
        return

    sudoku_json = response.json()
    sudoku_grid = sudoku_json["newboard"]["grids"][0]["value"]
    sudoku_solution = sudoku_json["newboard"]["grids"][0]["solution"]
    sudoku_difficulty = sudoku_json["newboard"]["grids"][0]["difficulty"]

    sudoku_grid_string = ''.join(str(num) for row in sudoku_grid for num in row)
    sudoku_solution_string = ''.join(str(num) for row in sudoku_solution for num in row)

    riddle = update_riddle(interaction.guild.id, interaction.user.id, sudoku_grid_string, sudoku_solution_string, True)

    await interaction.response.send_message("Heh. Good luck!", ephemeral=True)

    channel = interaction.guild.get_channel(guild.jail_channel)
    await channel.send(switch_sudoku_message(riddle, interaction.user, sudoku_difficulty))


class SetRole(str, enum.Enum):
    ModeratorRole = "moderator_role"
    InmateRole = "inmate_role"


@bot.tree.command(name="setrole", description="Set a server role")
@app_commands.describe(role="The role to set")
@app_commands.describe(value="The value to set")
async def setrole(interaction: Interaction, role: SetRole, value: Role):
    if not interaction.user.guild_permissions.administrator and not await bot.is_owner(interaction.user):
        await interaction.response.send_message("You are not authorised to run this command!", ephemeral=True)
        return

    if role is SetRole.ModeratorRole:
        update_guild(interaction.guild.id, i_moderator=value.id)
    else:
        update_guild(interaction.guild.id, i_inmate=value.id)

    await interaction.response.send_message("OK", ephemeral=True)


@bot.tree.command(name="setchannel", description="Set the jail channel")
@app_commands.describe(channel="The value to set")
async def setchannel(interaction: Interaction, channel: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator and not await bot.is_owner(interaction.user):
        await interaction.response.send_message("You are not authorised to run this command!", ephemeral=True)
        return

    update_guild(interaction.guild.id, i_jail=channel.id)

    await interaction.response.send_message("OK", ephemeral=True)


discord_logger = logging.getLogger('discord')
discord_logger.setLevel('DEBUG')
discord_logger.handlers.clear()
for s_logger in logger.loggers:
    discord_logger.addHandler(s_logger.handlers[0])

bot.run(env['DISCORD_TOKEN'], log_handler=None)