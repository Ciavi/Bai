from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord_timestamps import format_timestamp, TimestampType

from commands.messages import embed_configuration_error, embed_permissions_error
from commands.utils import is_guild_configured, is_user_organiser
from commands.view_raid import RaidView
from data.interface import create_raid
from data.models import Raid as RaidModel


class DatetimeConverter(app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, argument: str) -> datetime:
        try:
            date = datetime.strptime(argument, "%Y-%m-%d %H:%M")
            return date
        except ValueError:
            raise commands.BadArgument(f"Invalid date: {argument}")


class Raid(commands.Cog):
    group = app_commands.Group(name="raid", description="Raid organisation commands")

    def __init__(self, bot):
        self.bot = bot


class Starverse(Raid):
    group = app_commands.Group(name="starverse", description="Starverse commands")

    def __init__(self, bot):
        super().__init__(bot)


    @group.command(name="create", description="Create a new starverse raid")
    @app_commands.describe(apply_by="Applications close by")
    @app_commands.describe(happens_on="Raid scheduled to happen on")
    @app_commands.describe(title="Raid title")
    @app_commands.describe(description="Raid description")
    async def create(self, interaction: discord.Interaction,
                     apply_by: app_commands.Transform[
                         datetime, DatetimeConverter
                     ],
                     happens_on: app_commands.Transform[
                         datetime, DatetimeConverter
                     ],
                     title: str = None,
                     description: str = None):
        guild, is_configured = await is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not await is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        title = title or f"Starverse"
        title += f" ({happens_on.date().isoformat()})"
        description = description or f"Organised by <@{interaction.user.id}>\n"
        description += f"Happens on {format_timestamp(happens_on.timestamp(), TimestampType.LONG_DATETIME)}.\n Apply by {format_timestamp(apply_by.timestamp(), TimestampType.LONG_DATETIME)} ({format_timestamp(apply_by.timestamp(), TimestampType.RELATIVE)}).\n"

        raid: RaidModel = create_raid(i_guild=interaction.guild.id, i_user=interaction.user.id, s_title=title, s_description=description, d_apply_by=apply_by, d_happens_on=happens_on)

        embed = discord.Embed(title=title, description=description, color=discord.Color.random())
        embed.set_footer(text=f"Raid: `{raid.id}`")
        view = RaidView(user=interaction.user, raid_id=raid.id, timeout=apply_by.timestamp() - datetime.now().timestamp())

        await interaction.response.send_message(f"Created raid `{raid.id}`", ephemeral=True)
        message = await interaction.channel.send(embed=embed, view=view)
        view.message = message


class Kunlun(Raid):
    group = app_commands.Group(name="kunlun", description="Kunlun commands")

    def __init__(self, bot):
        super().__init__(bot)

    @group.command(name="create", description="Create a new kunlun raid")
    @app_commands.describe(apply_by="Applications close by")
    @app_commands.describe(happens_on="Raid scheduled to happen on")
    @app_commands.describe(title="Raid title")
    @app_commands.describe(description="Raid description")
    async def create(self, interaction: discord.Interaction,
                     apply_by: app_commands.Transform[
                         datetime, DatetimeConverter
                     ],
                     happens_on: app_commands.Transform[
                         datetime, DatetimeConverter
                     ],
                     title: str = None,
                     description: str = None):
        guild, is_configured = await is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not await is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        title = title or f"Kunlun"
        title += f" ({happens_on.date().isoformat()})"
        description = description or f"Organised by <@{interaction.user.id}>\n"
        description += f"Happens on {format_timestamp(happens_on.timestamp(), TimestampType.LONG_DATETIME)}.\n Apply by {format_timestamp(apply_by.timestamp(), TimestampType.LONG_DATETIME)} ({format_timestamp(apply_by.timestamp(), TimestampType.RELATIVE)}).\n"

        raid: RaidModel = create_raid(i_guild=interaction.guild.id, i_user=interaction.user.id, s_title=title,
                                      s_description=description, d_apply_by=apply_by, d_happens_on=happens_on)

        embed = discord.Embed(title=title, description=description, color=discord.Color.random())
        embed.set_footer(text=f"Raid: `{raid.id}`")
        view = RaidView(user=interaction.user, raid_id=raid.id,
                        timeout=apply_by.timestamp() - datetime.now().timestamp())

        await interaction.response.send_message(f"Created raid `{raid.id}`", ephemeral=True)
        message = await interaction.channel.send(embed=embed, view=view)
        view.message = message


async def setup(bot: Bot):
    await bot.add_cog(Starverse(bot))
    await bot.add_cog(Kunlun(bot))
