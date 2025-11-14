from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from commands.messages import embed_configuration_error, embed_permissions_error, embed_scheduled_message, \
    message_scheduled_jobs
from commands.utils import is_guild_configured, is_user_organiser, DatetimeConverter

class Scheduler(commands.Cog):
    group = app_commands.Group(name="schedule", description="Scheduler commands")

    def __init__(self, bot):
        self.bot = bot


    @group.command(name="list", description="List scheduled jobs")
    async def list(self, interaction: discord.Interaction):
        guild, is_configured = is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        await interaction.response.defer()

        jobs = self.bot.scheduler.get_jobs()
        messages = message_scheduled_jobs(interaction, jobs)
        await interaction.followup.send_message(content=messages)



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


    @group.command(name="cmessage", description="Schedule a message (via crontab) to be sent in the current channel")
    @app_commands.describe(cron="Cron expression (5 DIGIT ONLY)")
    @app_commands.describe(message="Message to be sent in the current channel")
    async def cmessage(self, interaction: discord.Interaction,
                       cron: str,
                       message: str):
        guild, is_configured = is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        self.bot.cronschedule_message(channel_id=interaction.channel.id, text=message, cron=cron)

async def setup(bot):
    await bot.add_cog(Scheduler(bot))
