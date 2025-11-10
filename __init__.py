import asyncio
import json
import logging
from os import environ as env

import discord
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import Member
from discord.ext import commands
from dotenv import load_dotenv
from quart import Quart, make_response, request

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


web = Quart(__name__)


def scheduler_listener(event):
    if event.exception:
        logger.critical(event.exception)
    else:
        logger.debug("Scheduler completed job successfully")


class Bai(commands.Bot):
    scheduler: AsyncIOScheduler

    async def setup_hook(self):
        self.loop.create_task(
            web.run_task(
                host='0.0.0.0', port=4443, certfile='./cert.pem', keyfile='./key.pem', debug=False
            )
        )

        jobstores = {
            'default': SQLAlchemyJobStore(url="sqlite:///jobs.sqlite")
        }
        job_defaults = {
            'coalesce': True
        }

        self.scheduler = AsyncIOScheduler(jobstores=jobstores, job_defaults=job_defaults)
        self.scheduler.add_listener(scheduler_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        self.scheduler.start()

        await self.load_extension('commands.cog_config')
        await self.load_extension('commands.cog_jail')
        await self.load_extension('commands.cog_premium')
        await self.load_extension('commands.cog_raid')
        await self.tree.sync()


bot = Bai(command_prefix='^', intents=intents)


@web.post("/ko-fi")
async def kofi():
    post_data = (await request.form).get('data')
    json_data = json.loads(post_data)

    if json_data['verification_token'] != env['KOFI_TOKEN']:
        return await make_response("Unauthorized", 403)

    asyncio.create_task(handle_kofi(json_data))

    return await make_response("OK", 200)


async def handle_kofi(data):
    # send json_data to main thread
    embed = p_embed_kofi(data)
    owner = await bot.fetch_user(int(env['OWNER']))
    await owner.send(embed=embed)


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}#{bot.user.discriminator}')
    initialise()


@bot.event
async def on_error(event, *args, **kwargs):
    logger.error(f'{event}: {", ".join(args)}\n\t{"\n\t".join(f"{k}: {v}" for k, v in kwargs.items())}')


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    pass


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if not before and not after:
        return

    if not before.guild and not after.guild:
        return

    guild, is_configured = is_guild_configured(before.guild.id or after.guild.id)

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
    guild, is_configured = is_guild_configured(message.guild.id)

    if not is_configured:
        return

    channel = message.guild.get_channel(guild.configuration['log_channel'])
    e, e_a = embed_message_delete(message)
    embeds = [e] + e_a

    await channel.send(embeds=embeds)


@bot.event
async def on_member_remove(member: Member):
    guild, is_configured = is_guild_configured(member.guild.id)

    if not is_configured:
        return

    channel = member.guild.get_channel(guild.configuration['log_channel'])
    await channel.send(embed=embed_member_leave_guild(member=member))


bot.run(env['DISCORD_TOKEN'], log_handler=None)