from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from commands.messages import embed_configuration_error, embed_permissions_error, embed_scheduled_message
from commands.utils import is_guild_configured, is_user_organiser, DatetimeConverter

class Scheduler(commands.Cog):
    group = app_commands.Group(name="schedule", description="Scheduler commands")

    def __init__(self, bot):
        self.bot = bot


    @group.command(name="message", description="Schedule a message to be sent in the current channel")
    @app_commands.describe(when="When to send the message")
    @app_commands.describe(message="Message to be sent in the current channel")
    async def message(self, interaction: discord.Interaction,
                      when: app_commands.Transform[
                          datetime, DatetimeConverter
                      ],
                      message: str):
        guild, is_configured = is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        self.bot.schedule_message(channel_id=interaction.channel.id, text=message, when=when)
        await interaction.response.send_message(embed=embed_scheduled_message(message, when), ephemeral=True)


async def setup(bot):
    await bot.add_cog(Scheduler(bot))
