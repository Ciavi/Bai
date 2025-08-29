from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from commands.utils import DatetimeConverter
from data.interface import create_subscriber, delete_subscriber


class Premium(commands.Cog):
    group = app_commands.Group(name="premium", description="Premium commands")

    def __init__(self, bot):
        self.bot = bot


    @group.command(name="licence")
    @app_commands.describe(guild="The licenced guild")
    @app_commands.describe(since="Subscription start date")
    @app_commands.describe(until="Subscription end date")
    async def licence(self, interaction: discord.Interaction,
                      guild: int,
                      since: app_commands.Transform[
                          datetime, DatetimeConverter
                      ],
                      until: app_commands.Transform[
                          datetime, DatetimeConverter
                      ]):
        if not self.bot.is_owner(interaction.user):
            await interaction.response.send_message("You are not authorised to run this command!", ephemeral=True)
            return

        _ = create_subscriber(guild, since, until)

        await interaction.response.send_message(f"Guild {guild} subscribed until {until}")


    @group.command(name="revoke")
    @app_commands.describe(guild="The guild whose licence to revoke")
    async def revoke(self, interaction: discord.Interaction, guild: int):
        if not self.bot.is_owner(interaction.user):
            await interaction.response.send_message("You are not authorised to run this command!", ephemeral=True)
            return

        delete_subscriber(guild)

        await interaction.response.send_message(f"Guild {guild} unsubscribed")

