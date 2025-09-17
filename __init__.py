import json
import logging
import urllib.parse
from os import environ as env

import discord
from discord import Member
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask, make_response, request

import system.configuration
import system.historian
from commands.messages import embed_member_leave_guild, embed_message_delete, embeds_message_edit, p_embed_kofi
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
        await self.load_extension('commands.cog_config')
        await self.load_extension('commands.cog_jail')
        await self.load_extension('commands.cog_premium')
        await self.load_extension('commands.cog_raid')
        await self.tree.sync()

web = Flask(__name__)
bot = Bai(command_prefix='^', intents=intents)

@web.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def home():
    return make_response(None, 403)

@web.route('/ko-fi', methods=['POST'])
async def kofi():
    post_data = request.form.get('data')
    json_data = json.loads(post_data)

    print(json_data)

    if json_data['verification_token'] != env['KOFI_TOKEN']:
        return make_response(None, 403)

    embed = p_embed_kofi(json_data)
    owner = await bot.fetch_user(bot.owner_id)
    await owner.send(embed=embed)

    return make_response(None, 200)


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}#{bot.user.discriminator}')
    initialise()
    web.run(host='0.0.0.0', port=4443, ssl_context=('cert.pem', 'key.pem'))

@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    guild, is_configured = await is_guild_configured(before.guild.id)

    if not is_configured:
        return

    channel = before.guild.get_channel(guild.configuration['log_channel'])
    b, b_a, a, a_a = embeds_message_edit(before, after)

    embeds_b = [b] + b_a
    embeds_a = [a] + a_a

    await channel.send(embeds=embeds_b)
    await channel.send(embeds=embeds_a)


@bot.event
async def on_message_delete(message: discord.Message):
    guild, is_configured = await is_guild_configured(message.guild.id)

    if not is_configured:
        return

    channel = message.guild.get_channel(guild.configuration['log_channel'])
    e, e_a = embed_message_delete(message)
    embeds = [e] + e_a

    await channel.send(embeds=embeds)


@bot.event
async def on_member_remove(member: Member):
    guild, is_configured = await is_guild_configured(member.guild.id)

    if not is_configured:
        return

    channel = member.guild.get_channel(guild.configuration['log_channel'])
    await channel.send(embed=embed_member_leave_guild(member=member))

bot.run(env['DISCORD_TOKEN'], log_handler=None)
