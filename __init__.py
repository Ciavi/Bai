import logging
from os import environ as env

import discord
from discord import Member
from discord.ext import commands
from dotenv import load_dotenv

import system.configuration
import system.historian
from commands.messages import embed_member_leave_guild, embed_message_delete, embeds_message_edit
from commands.utils import is_guild_configured
from data.interface import initialise

load_dotenv()

intents = discord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True

configuration = system.configuration.Configuration('conf.json')
logger = system.historian.Logging(configuration)

discord_logger = logging.getLogger('discord')
discord_logger.setLevel('DEBUG')
discord_logger.handlers.clear()
for s_logger in logger.loggers:
    discord_logger.addHandler(s_logger.handlers[0])


class Bai(commands.Bot):
    async def setup_hook(self):
        await self.load_extension("commands.cog_config")
        await self.load_extension("commands.cog_jail")
        await self.load_extension("commands.cog_raid")
        await self.tree.sync()


bot = Bai(command_prefix='^', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}#{bot.user.discriminator}')
    initialise()


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    guild, is_configured = await is_guild_configured(before.guild.id)

    if not is_configured:
        return

    channel = before.guild.get_channel(guild.configuration['log_channel'])
    b, b_a, a, a_a = embeds_message_edit(before, after)

    await channel.send(content="", embeds=[b, b_a])
    await channel.send(content="", embeds=[a, a_a])


@bot.event
async def on_message_delete(message: discord.Message):
    guild, is_configured = await is_guild_configured(message.guild.id)

    if not is_configured:
        return

    channel = message.guild.get_channel(guild.configuration['log_channel'])
    e, e_a = embed_message_delete(message)

    await channel.send(content="", embeds=[e, e_a])


@bot.event
async def on_member_remove(member: Member):
    guild, is_configured = await is_guild_configured(member.guild.id)

    if not is_configured:
        return

    channel = member.guild.get_channel(guild.configuration['log_channel'])
    await channel.send(embed=embed_member_leave_guild(member=member))

bot.run(env['DISCORD_TOKEN'], log_handler=None)