from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from commands.utils import DatetimeConverter


class Premium(commands.Cog):
    group = app_commands.Group(name="premium", description="Premium commands")

    def __init__(self, bot):
        self.bot = bot


    @group.command(name="licence")
    @app_commands.describe(since="Subscription start date")
    @app_commands.describe(until="Subscription end date")
    async def licence(self, interaction: discord.Interaction,
                      since: app_commands.Transform[
                          datetime, DatetimeConverter
                      ],
                      until: app_commands.Transform[
                          datetime, DatetimeConverter
                      ]):
        if not self.bot.is_owner(interaction.user):
            await interaction.response.send_message("You are not authorised to run this command!", ephemeral=True)
            return

