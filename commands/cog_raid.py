from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Bot
from discord_timestamps import format_timestamp, TimestampType
import webcolors

from commands.messages import embed_configuration_error, embed_permissions_error
from commands.utils import is_guild_configured, is_user_organiser, DatetimeConverter
from commands.view_raid import RaidView, ClashView
from data.interface import create_raid, update_raid
from data.models import Raid as RaidModel


class Raid(commands.Cog):
    group = app_commands.Group(name="raid", description="Raid organisation commands")

    def __init__(self, bot: Bot):
        self.bot = bot


class Starverse(Raid):
    group = app_commands.Group(name="starverse", description="Starverse commands")

    def __init__(self, bot):
        super().__init__(bot)

        self.message_menu = app_commands.ContextMenu(callback=self.close, name="Close sign-ups")
        # self.message_menu.error(self.count_error)
        self.bot.tree.add_command(self.message_menu)


    @group.command(name="create", description="Create a new starverse raid")
    @app_commands.describe(apply_by="Applications close by")
    @app_commands.describe(happens_on="Raid scheduled to happen on")
    @app_commands.describe(colour="Pick a colour :)")
    @app_commands.describe(title="Raid title")
    @app_commands.describe(description="Raid description")
    async def create(self, interaction: discord.Interaction,
                     apply_by: app_commands.Transform[
                         datetime, DatetimeConverter
                     ],
                     happens_on: app_commands.Transform[
                         datetime, DatetimeConverter
                     ],
                     colour: str,
                     title: str = None,
                     description: str = None):
        guild, is_configured = is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        c_hex = webcolors.name_to_hex(colour.lower())[1:]
        thumbnail = f"https://singlecolorimage.com/get/{c_hex}/128x128"
        image = f"https://singlecolorimage.com/get/{c_hex}/768x128"

        title = title or f"Starverse"
        title += f" ({happens_on.date().isoformat()})"
        description = description or f"Organised by <@{interaction.user.id}>"
        description += f"\nHappens on {format_timestamp(happens_on.timestamp(), TimestampType.LONG_DATETIME)}.\n Apply by {format_timestamp(apply_by.timestamp(), TimestampType.LONG_DATETIME)} ({format_timestamp(apply_by.timestamp(), TimestampType.RELATIVE)}).\n"

        raid: RaidModel = create_raid(i_guild=interaction.guild.id, i_user=interaction.user.id, s_title=title, s_description=description, d_apply_by=apply_by, d_happens_on=happens_on)

        embed = discord.Embed(title=title, description=description, color=discord.Color.from_str(f"#{c_hex}"))
        embed.set_thumbnail(url=thumbnail)
        embed.set_image(url=image)
        embed.set_footer(text=f"Raid: {raid.id}")

        await interaction.response.send_message(f"Created raid `{raid.id}`", ephemeral=True)
        message = await interaction.channel.send(embed=embed)

        view = RaidView(user=interaction.user, raid_id=raid.id, message=message,
                        timeout=apply_by.timestamp() - datetime.now().timestamp())

        await message.edit(view=view)


    async def close(self, interaction: discord.Interaction, message: discord.Message):
        guild, is_configured = is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        if message.embeds is not None and len(message.embeds) > 0 and message.author == self.bot.user:
            embed = message.embeds[0]

            if embed.footer.text.startswith("Raid:"):
                r_id = int(embed.footer.text.replace("Raid:", "").strip())
                _ = update_raid(i_raid=r_id, d_apply_by=datetime.now())

                await message.edit(view=None)
                await interaction.response.send_message(f"Sign-ups for raid #{r_id} were closed successfully.")
                return

        await interaction.response.send_message(f"Not a raid :)", ephemeral=True)
        return


class Kunlun(Raid):
    group = app_commands.Group(name="kunlun", description="Kunlun commands")

    def __init__(self, bot):
        super().__init__(bot)

    @group.command(name="create", description="Create a new kunlun raid")
    @app_commands.describe(apply_by="Applications close by")
    @app_commands.describe(happens_on="Raid scheduled to happen on")
    @app_commands.describe(colour="Pick a colour :)")
    @app_commands.describe(title="Raid title")
    @app_commands.describe(description="Raid description")
    async def create(self, interaction: discord.Interaction,
                     apply_by: app_commands.Transform[
                         datetime, DatetimeConverter
                     ],
                     happens_on: app_commands.Transform[
                         datetime, DatetimeConverter
                     ],
                     colour: str,
                     title: str = None,
                     description: str = None):
        guild, is_configured = is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        c_hex = webcolors.name_to_hex(colour.lower())[1:]
        thumbnail = f"https://singlecolorimage.com/get/{c_hex}/128x128"
        image = f"https://singlecolorimage.com/get/{c_hex}/768x128"

        title = title or f"Kunlun"
        title += f" ({happens_on.date().isoformat()})"
        description = description or f"Organised by <@{interaction.user.id}>"
        description += f"\nHappens on {format_timestamp(happens_on.timestamp(), TimestampType.LONG_DATETIME)}.\n Apply by {format_timestamp(apply_by.timestamp(), TimestampType.LONG_DATETIME)} ({format_timestamp(apply_by.timestamp(), TimestampType.RELATIVE)}).\n"

        raid: RaidModel = create_raid(i_guild=interaction.guild.id, i_user=interaction.user.id, s_title=title,
                                      s_description=description, d_apply_by=apply_by, d_happens_on=happens_on)

        embed = discord.Embed(title=title, description=description, color=discord.Color.from_str(f"#{c_hex}"))
        embed.set_thumbnail(url=thumbnail)
        embed.set_image(url=image)
        embed.set_footer(text=f"Raid: {raid.id}")

        await interaction.response.send_message(f"Created raid `{raid.id}`", ephemeral=True)
        message = await interaction.channel.send(embed=embed)

        view = RaidView(user=interaction.user, raid_id=raid.id, message=message,
                        timeout=apply_by.timestamp() - datetime.now().timestamp())

        await message.edit(view=view)

        async def close(self, interaction: discord.Interaction, message: discord.Message):
            guild, is_configured = is_guild_configured(interaction.guild.id)

            if not is_configured:
                await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
                return

            if not is_user_organiser(guild, interaction.user):
                await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
                return

            if message.embeds is not None and len(message.embeds) > 0 and message.author == self.bot.user:
                embed = message.embeds[0]

                if embed.footer.text.startswith("Raid:"):
                    id = int(embed.footer.text.replace("Raid:", "").strip())
                    _ = update_raid(i_raid=id, d_apply_by=datetime.now())

                    await message.edit(view=None)
                    await interaction.response.send_message(f"Sign-ups for raid #{id} were closed successfully.")
                    return

            await interaction.response.send_message(f"Not a raid :)", ephemeral=True)
            return


class Clash(Raid):
    group = app_commands.Group(name="clash", description="clash commands")

    def __init__(self, bot):
        super().__init__(bot)

    @group.command(name="create", description="Create a new sect clash")
    @app_commands.describe(apply_by="Applications close by")
    @app_commands.describe(happens_on="Raid scheduled to happen on")
    @app_commands.describe(title="Raid title")
    @app_commands.describe(description="Raid description")
    @app_commands.describe(arrays="Number of arrays")
    async def create(self, interaction: discord.Interaction,
                     apply_by: app_commands.Transform[
                         datetime, DatetimeConverter
                     ],
                     happens_on: app_commands.Transform[
                         datetime, DatetimeConverter
                     ],
                     title: str = None,
                     description: str = None,
                     arrays: app_commands.Range[int, 1, 4] = 3):
        guild, is_configured = is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        title = title or f"Sect Clash"
        title += f" ({happens_on.date().isoformat()})"
        description = description or f"Organised by <@{interaction.user.id}>\n"
        description += f"Happens on {format_timestamp(happens_on.timestamp(), TimestampType.LONG_DATETIME)}.\n Apply by {format_timestamp(apply_by.timestamp(), TimestampType.LONG_DATETIME)} ({format_timestamp(apply_by.timestamp(), TimestampType.RELATIVE)}).\n"

        raid: RaidModel = create_raid(i_guild=interaction.guild.id, i_user=interaction.user.id, s_title=title,
                                      s_description=description, d_apply_by=apply_by, d_happens_on=happens_on)

        embed = discord.Embed(title=title, description=description, color=discord.Color.random())
        embed.set_footer(text=f"Raid: {raid.id}")

        await interaction.response.send_message(f"Created raid `{raid.id}`", ephemeral=True)
        message = await interaction.channel.send(content="Incoming raid...")

        view = ClashView(user=interaction.user, raid_id=raid.id, message=message, arrays=arrays,
                        timeout=apply_by.timestamp() - datetime.now().timestamp())

        await message.edit(embed=embed, view=view)


async def setup(bot: Bot):
    await bot.add_cog(Clash(bot))
    await bot.add_cog(Starverse(bot))
    await bot.add_cog(Kunlun(bot))
