from discord import Embed, Color, Member
from requests import Response

from commands.utils import display_sudoku
from data.models import Guild, Riddle


def embed_api_error(response: Response):
    embed = Embed(color=Color.red(), title=f"API Error ({response.status_code})")
    embed.description = f"```\n{response.text}```"
    return embed


def embed_configuration_error(guild: Guild):
    embed = Embed(color=Color.red(), title=f"Guild `{guild.id}` is not configured correctly!")
    embed.description = (f"All the following variables must be set:\n"
                         f"`moderator_role`: `<@&{guild.configuration['moderator_role']}>`\n"
                         f"`inmate_role`: `<@&{guild.configuration['inmate_role']}>`\n"
                         f"`jail_channel`: `<#{guild.configuration['jail_channel']}>`\n"
                         f"`log_channel`: `<#{guild.configuration['log_channel']}>`\n`")
    return embed


def embed_member_leave_guild(member: Member):
    embed = Embed(color=Color.red(), title=f"<@!{member.id}> left")
    embed.description = f"Joined at {member.joined_at}"
    embed.set_thumbnail(url=member.avatar.url)

    return embed


def embed_permissions_error(guild: Guild):
    embed = Embed(color=Color.red(), title=f"You don't have permission to use this command!")
    embed.description = f"You need the role <@{guild.configuration['moderator_role']}> to use this command."
    return embed


def message_imprisonment(riddle: Riddle, member: Member):
    return (f"## Welcome to the Dungeon <@!{member.id}> 😏\n"
            f"### Solve the following riddle to get out.\n"
            f"-# Use `/solve <answer>` to solve.\n"
            f"-# Use `/sudoku` to switch to a sudoku if your brain is melting.\n"
            f"> {riddle.text}")


def message_right(riddle: Riddle, is_user_solution: bool = False):
    if riddle.is_sudoku:
        solution_array = [list(map(int, riddle.solution[i:i + 9])) for i in range(0, len(riddle.solution), 9)]
        solution_pretty = display_sudoku(solution_array)

        if is_user_solution:
            return (f"Your solution is also valid! Ours is:\n"
                    f"```{solution_pretty}```\n"
                    f"You have regained your freedom. You'll be freed in 10 seconds.")

        return (f"Good job! The solution was\n"
                f"```{solution_pretty}```\n"
                f"You have regained your freedom. You'll be freed in 10 seconds.")

    return(f"Good job! The answer was `{riddle.solution}`.\n"
           f"You have regained your freedom. You'll be freed in 10 seconds.")


def message_switch_sudoku(riddle: Riddle, member: Member, difficulty: str):
    grid_array = [list(map(int, riddle.text[i:i+9])) for i in range(0, len(riddle.text), 9)]
    grid_pretty = display_sudoku(grid_array)

    return (f"## Damn <@!{member.id}>, you picked the sudoku instead!\n"
                f"-# Use `/solve <answer>` to solve.\n"
                f"-# The solution is to be given in a string format, ***row-by-row***.\n"
                f"```{grid_pretty}```\n"
                f"Difficulty: `{difficulty}`")


def message_wrong(riddle: Riddle):
    if riddle.is_sudoku:
        sudoku_array = [list(map(int, riddle.text[i:i + 9])) for i in range(0, len(riddle.text), 9)]
        sudoku_pretty = display_sudoku(sudoku_array)
        return (f"Wrong! Try again!\n"
                f"```{sudoku_pretty}```")

    return(f"Wrong! Try again!\n"
           f"> {riddle.text}")