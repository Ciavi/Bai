import asyncio
import enum
from datetime import datetime

import discord
import logging
import requests

from discord import app_commands, Member, Embed, Color, Interaction, Role, User
from requests import Response

from sentence_transformers import SentenceTransformer, util

import system.configuration
import system.historian

from os import environ as env
from discord.ext import commands
from dotenv import load_dotenv

from commands.cog_config import Configuration
from commands.cog_jail import Jail
from commands.messages import embed_member_leave_guild
from commands.utils import is_guild_configured
from data.interface import initialise, create_guild, update_guild, create_riddle, read_riddle, delete_riddle, \
    update_riddle
from data.models import Riddle, Guild

load_dotenv()

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True

configuration = system.configuration.Configuration('conf.json')
logger = system.historian.Logging(configuration)

bot = commands.Bot(command_prefix='^', intents=intents)

async def setup_hook():
    await bot.tree.sync()
    await bot.add_cog(Configuration(bot))
    await bot.add_cog(Jail(bot))

bot.setup_hook = setup_hook


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}#{bot.user.discriminator}')
    initialise()


@bot.event
async def on_member_remove(member: Member):
    guild, is_configured = is_guild_configured(member.guild.id)

    if not is_configured:
        return

    channel = member.guild.get_channel(guild.configuration['log_channel'])
    await channel.send(embed=embed_member_leave_guild(member=member))


discord_logger = logging.getLogger('discord')
discord_logger.setLevel('DEBUG')
discord_logger.handlers.clear()
for s_logger in logger.loggers:
    discord_logger.addHandler(s_logger.handlers[0])

bot.run(env['DISCORD_TOKEN'], log_handler=None)