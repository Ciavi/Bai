import dateparser
from datetime import datetime

import discord
from discord import Member, app_commands
from discord.ext import commands

from data.interface import GuildWrapper, create_guild
from data.models import Guild


async def is_guild_configured(guild_id: int) -> tuple[Guild, bool]:
    guild: Guild = create_guild(guild_id)
    is_not_none: bool = guild.configuration is not None

    return guild, is_not_none


async def is_user_imprisoned(guild: Guild, member: Member) -> bool:
    return any(role.id == guild.configuration['inmate_role'] for role in member.roles)


async def is_user_organiser(guild: Guild, member: Member) -> bool:
    return any(role.id == guild.configuration['organiser_role'] for role in member.roles)


async def is_user_warden(guild: Guild, member: Member) -> bool:
    return any(role.id == guild.configuration['warden_role'] for role in member.roles)


def is_valid_user_solution(puzzle, solution):
    def is_valid_group(group):
        return sorted(group) == list(range(1, 10))

    # Check that original puzzle values are preserved
    for i in range(9):
        for j in range(9):
            if puzzle[i][j] != 0 and puzzle[i][j] != solution[i][j]:
                return False

    # Check rows and columns
    for i in range(9):
        row = solution[i]
        col = [solution[r][i] for r in range(9)]
        if not is_valid_group(row) or not is_valid_group(col):
            return False

    # Check 3x3 subgrids
    for box_row in range(0, 9, 3):
        for box_col in range(0, 9, 3):
            block = [solution[r][c] for r in range(box_row, box_row + 3)
                                      for c in range(box_col, box_col + 3)]
            if not is_valid_group(block):
                return False

    return True


def display_sudoku(grid) -> str:
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


class DatetimeConverter(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, argument: str) -> datetime:
        try:
            date = dateparser.parse(argument)
            return date
        except ValueError:
            raise commands.BadArgument(f"Invalid date: {argument}")