from datetime import datetime, timedelta

import discord
from discord import app_commands, Role
from discord.ext import commands
from discord_timestamps import format_timestamp, TimestampType
import webcolors

from commands.messages import embed_configuration_error, embed_permissions_error, message_raid_starting_in, \
    message_raid_now, embed_scheduled_message
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

        self.bot.schedule_message(channel_id=interaction.channel.id, message=message)
        await interaction.response.send_message(embed=embed_scheduled_message(message, when), ephemeral=True)


async def setup(bot):
    await bot.add_cog(Scheduler(bot))
