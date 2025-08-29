import enum

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot

from data.interface import update_guild


class Configuration(commands.Cog):
    group = app_commands.Group(name="configure", description="Configuration commands")

    def __init__(self, bot: Bot):
        self.bot = bot


    class Channel(str, enum.Enum):
        JailChannel = "jail_channel"
        LogChannel = "log_channel"


    class Role(str, enum.Enum):
        InmateRole = "inmate_role"
        OrganiserRole = "organiser_role"
        WardenRole = "warden_role"


    async def __is_admin_or_owner(self, interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator or await self.bot.is_owner(interaction.user)


    @group.command(name="channel", description="Configure a channel")
    @app_commands.describe(channel="The channel to configure")
    @app_commands.describe(value="The value to assign")
    async def channel(self, interaction: discord.Interaction, channel: Channel, value: discord.TextChannel):
        if not await self.__is_admin_or_owner(interaction):
            await interaction.response.send_message("You are not authorised to run this command!", ephemeral=True)
            return

        temp_config: dict = {channel: value.id}
        update_guild(interaction.guild.id, o_configuration=temp_config)

        await interaction.response.send_message("OK", ephemeral=True)


    @group.command(name="role", description="Configure a role")
    @app_commands.describe(role="The role to configure")
    @app_commands.describe(value="The value to assign")
    async def role(self, interaction: discord.Interaction, role: Role, value: discord.Role):
        if not await self.__is_admin_or_owner(interaction):
            await interaction.response.send_message("You are not authorised to run this command!", ephemeral=True)
            return

        temp_config: dict = {role: value.id}
        update_guild(interaction.guild.id, o_configuration=temp_config)

        await interaction.response.send_message("OK", ephemeral=True)


async def setup(bot: Bot):
    await bot.add_cog(Configuration(bot))