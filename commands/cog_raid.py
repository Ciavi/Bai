import enum
from datetime import datetime, timedelta

import discord
from discord import app_commands, Member, Role, Message
from discord.ext import commands
from discord_timestamps import format_timestamp, TimestampType
import webcolors

from __init__ import Bai

from commands.messages import embed_configuration_error, embed_permissions_error, message_raid_starting_in, \
    message_raid_now
from commands.utils import is_guild_configured, is_user_organiser, DatetimeConverter
from commands.view_raid import RaidView, ClashView
from data.interface import create_raid, update_raid, get_raid_supports, get_raid_leaders, get_raid_backup_leaders
from data.models import Raid as RaidModel


class RaidSchedule:
    What: str
    When: datetime
    Pre: datetime
    Who: int


CSS_COLOR_NAMES = [
    'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige',
    'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown',
    'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral',
    'cornflowerblue', 'cornsilk', 'crimson', 'cyan', 'darkblue',
    'darkcyan', 'darkgoldenrod', 'darkgray', 'darkgrey', 'darkgreen',
    'darkkhaki', 'darkmagenta', 'darkolivegreen', 'darkorange',
    'darkorchid', 'darkred', 'darksalmon', 'darkseagreen',
    'darkslateblue', 'darkslategray', 'darkslategrey', 'darkturquoise',
    'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dimgrey',
    'dodgerblue', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia',
    'gainsboro', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'grey',
    'green', 'greenyellow', 'honeydew', 'hotpink', 'indianred', 'indigo',
    'ivory', 'khaki', 'lavender', 'lavenderblush', 'lawngreen',
    'lemonchiffon', 'lightblue', 'lightcoral', 'lightcyan',
    'lightgoldenrodyellow', 'lightgray', 'lightgrey', 'lightgreen',
    'lightpink', 'lightsalmon', 'lightseagreen', 'lightskyblue',
    'lightslategray', 'lightslategrey', 'lightsteelblue', 'lightyellow',
    'lime', 'limegreen', 'linen', 'magenta', 'maroon', 'mediumaquamarine',
    'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen',
    'mediumslateblue', 'mediumspringgreen', 'mediumturquoise',
    'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose',
    'moccasin', 'navajowhite', 'navy', 'oldlace', 'olive', 'olivedrab',
    'orange', 'orangered', 'orchid', 'palegoldenrod', 'palegreen',
    'paleturquoise', 'palevioletred', 'papayawhip', 'peachpuff', 'peru',
    'pink', 'plum', 'powderblue', 'purple', 'red', 'rosybrown',
    'royalblue', 'saddlebrown', 'salmon', 'sandybrown', 'seagreen',
    'seashell', 'sienna', 'silver', 'skyblue', 'slateblue', 'slategray',
    'slategrey', 'snow', 'springgreen', 'steelblue', 'tan', 'teal',
    'thistle', 'tomato', 'turquoise', 'violet', 'wheat', 'white',
    'whitesmoke', 'yellow', 'yellowgreen'
]

async def colour_autocomplete(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return [app_commands.Choice(name=option, value=option) for option in CSS_COLOR_NAMES if option.lower().startswith(current.lower())][:25]


class Raid(commands.Cog):
    group = app_commands.Group(name="raid", description="Raid organisation commands")

    def __init__(self, bot: Bai):
        self.bot = bot

    async def send_starting_soon(self, message: Message, raid: RaidModel, ping: Role):
        await message.channel.send(message_raid_starting_in(raid, ping))

    async def send_now(self, message: Message, raid: RaidModel, ping: Role):
        await message.channel.send(message_raid_now(raid, ping))


class Starverse(Raid):
    group = app_commands.Group(name="starverse", description="Starverse commands")

    def __init__(self, bot):
        super().__init__(bot)

        self.ctx_clarify = app_commands.ContextMenu(callback=self.clarify, name="Show names")
        self.ctx_close = app_commands.ContextMenu(callback=self.close, name="Close sign-ups")
        # self.message_menu.error(self.count_error)
        self.bot.tree.add_command(self.ctx_clarify)
        self.bot.tree.add_command(self.ctx_close)


    @group.command(name="create", description="Create a new starverse raid")
    @app_commands.describe(apply_by="Applications close by")
    @app_commands.describe(happens_on="Raid scheduled to happen on")
    @app_commands.describe(colour="Pick a colour :)")
    @app_commands.autocomplete(colour=colour_autocomplete)
    @app_commands.describe(ping="Role to be pinged")
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
                     ping: Role = None,
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

        if ping is not None:
            self.bot.scheduler.add_job(func=self.send_starting_soon, args=[message, raid, ping], trigger="date", run_date=(happens_on - timedelta(hours=1)))
            self.bot.scheduler.add_job(func=self.send_now, args=[message, raid, ping], trigger="date", run_date=happens_on)

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

    async def clarify(self, interaction: discord.Interaction, message: discord.Message):
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
                raid_id = int(embed.footer.text.replace("Raid:", "").strip())

                leaders: list[int] | None = get_raid_leaders(raid_id)
                supports: list[int] | None = get_raid_supports(raid_id)

                s_leaders: list[str] = [
                    interaction.guild.get_member(leader).nick or interaction.guild.get_member(leader).global_name for
                    leader in
                    leaders]
                s_supports: list[str] = [
                    interaction.guild.get_member(support).nick or interaction.guild.get_member(support).global_name for
                    support
                    in supports]

                text = f"# Raid#{raid_id}\nLeader(s): " + ", ".join(s_leaders) + "\nSupport(s): " + ", ".join(
                    s_supports)

                await interaction.response.send_message(content=text, ephemeral=True)
                return

        await interaction.response.send_message(f"Not a raid :)", ephemeral=True)

    @group.command(name="list", description="List subscribers for starverse")
    @app_commands.describe(raid_id="Raid id")
    async def list(self, interaction: discord.Interaction,
                   raid_id: int):
        guild, is_configured = is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        leaders: list[int] | None = get_raid_leaders(raid_id)
        supports: list[int] | None = get_raid_supports(raid_id)

        s_leaders: list[str] = [
            interaction.guild.get_member(leader).nick or interaction.guild.get_member(leader).global_name for leader in
            leaders]
        s_supports: list[str] = [
            interaction.guild.get_member(support).nick or interaction.guild.get_member(support).global_name for support
            in supports]

        text = f"# Raid#{raid_id}\nLeader(s): " + ", ".join(s_leaders) + "\nSupport(s): " + ", ".join(s_supports)

        await interaction.response.send_message(content=text, ephemeral=True)


class Kunlun(Raid):
    group = app_commands.Group(name="kunlun", description="Kunlun commands")

    def __init__(self, bot):
        super().__init__(bot)

    @group.command(name="create", description="Create a new kunlun raid")
    @app_commands.describe(apply_by="Applications close by")
    @app_commands.describe(happens_on="Raid scheduled to happen on")
    @app_commands.describe(colour="Pick a colour :)")
    @app_commands.autocomplete(colour=colour_autocomplete)
    @app_commands.describe(ping="Role to be pinged")
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
                     ping: Role = None,
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

        if ping is not None:
            self.bot.scheduler.add_job(func=self.send_starting_soon, args=[message, raid, ping], trigger="date", run_date=(happens_on - timedelta(hours=1)))
            self.bot.scheduler.add_job(func=self.send_now, args=[message, raid, ping], trigger="date", run_date=happens_on)

        await message.edit(view=view)

    @group.command(name="list", description="List subscribers for kunlun")
    @app_commands.describe(raid_id="Raid id")
    async def list(self, interaction: discord.Interaction,
                   raid_id: int):
        guild, is_configured = is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        leaders: list[int] | None = get_raid_leaders(raid_id)
        supports: list[int] | None = get_raid_supports(raid_id)

        s_leaders: list[str] = [
            interaction.guild.get_member(leader).nick or interaction.guild.get_member(leader).global_name for leader in
            leaders]
        s_supports: list[str] = [
            interaction.guild.get_member(support).nick or interaction.guild.get_member(support).global_name for support
            in supports]

        text = f"# Raid#{raid_id}\nLeader(s): " + ", ".join(s_leaders) + "\nSupport(s): " + ", ".join(s_supports)

        await interaction.response.send_message(content=text, ephemeral=True)


class Clash(Raid):
    group = app_commands.Group(name="clash", description="clash commands")

    def __init__(self, bot):
        super().__init__(bot)

    @group.command(name="create", description="Create a new sect clash")
    @app_commands.describe(apply_by="Applications close by")
    @app_commands.describe(happens_on="Raid scheduled to happen on")
    @app_commands.describe(ping="Role to be pinged")
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
                     ping: Role = None,
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
        description = description or f"Organised by <@{interaction.user.id}>"
        description += f"\nHappens on {format_timestamp(happens_on.timestamp(), TimestampType.LONG_DATETIME)}.\n Apply by {format_timestamp(apply_by.timestamp(), TimestampType.LONG_DATETIME)} ({format_timestamp(apply_by.timestamp(), TimestampType.RELATIVE)}).\n"

        raid: RaidModel = create_raid(i_guild=interaction.guild.id, i_user=interaction.user.id, s_title=title,
                                      s_description=description, d_apply_by=apply_by, d_happens_on=happens_on)

        embed = discord.Embed(title=title, description=description, color=discord.Color.random())
        embed.set_footer(text=f"Raid: {raid.id}")

        await interaction.response.send_message(f"Created raid `{raid.id}`", ephemeral=True)
        message = await interaction.channel.send(content="Incoming raid...")

        view = ClashView(user=interaction.user, raid_id=raid.id, message=message, arrays=arrays,
                        timeout=apply_by.timestamp() - datetime.now().timestamp())

        if ping is not None:
            self.bot.scheduler.add_job(func=self.send_starting_soon, args=[message, raid, ping], trigger="date", run_date=(happens_on - timedelta(hours=1)))
            self.bot.scheduler.add_job(func=self.send_now, args=[message, raid, ping], trigger="date", run_date=happens_on)

        await message.edit(embed=embed, view=view)

    @group.command(name="list", description="List subscribers for sect clash")
    @app_commands.describe(raid_id="Raid id")
    async def list(self, interaction: discord.Interaction,
                   raid_id: int):
        guild, is_configured = is_guild_configured(interaction.guild.id)

        if not is_configured:
            await interaction.response.send_message(embed=embed_configuration_error(guild), ephemeral=True)
            return

        if not is_user_organiser(guild, interaction.user):
            await interaction.response.send_message(embed=embed_permissions_error(guild), ephemeral=True)
            return

        leaders: list[int] | None = get_raid_leaders(raid_id)
        backups: list[int] | None = get_raid_backup_leaders(raid_id)
        supports: list[int] | None = get_raid_supports(raid_id)

        s_leaders: list[str] = [interaction.guild.get_member(leader).nick or interaction.guild.get_member(leader).global_name for leader in leaders]
        s_backups: list[str] = [interaction.guild.get_member(backup).nick or interaction.guild.get_member(backup).global_name for backup in backups]
        s_supports: list[str] = [interaction.guild.get_member(support).nick or interaction.guild.get_member(support).global_name for support in supports]

        text = (f"# Raid#{raid_id}\nLeader(s): " + ", ".join(s_leaders) +
                "\nBackup(s): " + ", ".join(s_backups) +
                "\nSupport(s): " + ", ".join(s_supports))

        await interaction.response.send_message(content=text, ephemeral=True)


async def setup(bot: Bai):
    await bot.add_cog(Clash(bot))
    await bot.add_cog(Starverse(bot))
    await bot.add_cog(Kunlun(bot))
