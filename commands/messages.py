from datetime import datetime

import discord
from apscheduler.job import Job
from discord import Embed, Color, Member, Message, Role
from discord_timestamps import format_timestamp, TimestampType
from requests import Response
from table2ascii import table2ascii as t2a, PresetStyle

from commands.utils import display_sudoku
from data.interface import read_raid
from data.models import Guild, Raid, Riddle


def embed_api_error(response: Response):
    embed = Embed(color=Color.red(), title=f"API Error ({response.status_code})")
    embed.description = f"```\n{response.text}```"
    return embed


def embed_configuration_error(guild: Guild):
    embed = Embed(color=Color.red(), title=f"Guild `{guild.id}` is not configured correctly!")
    embed.description = (f"All the following variables must be set:\n"
                         f"`moderator_role`: `<@&{guild.configuration['moderator_role']}>`\n"
                         f"`inmate_role`: `<@&{guild.configuration['inmate_role']}>`\n"
                         f"`jail_channel`: `<#{guild.configuration['jail_channel']}>`\n"
                         f"`log_channel`: `<#{guild.configuration['log_channel']}>`\n`")
    return embed


def embed_member_leave_guild(member: Member):
    embed = Embed(color=Color.red(), title=f"{member.name} left")
    embed.description = f"{member.mention} left us."
    embed.add_field(name=f"Joined", value=f"{member.joined_at}")
    embed.set_thumbnail(url=member.avatar.url)

    return embed


def embed_message_delete(message: Message):
    attachments = []

    embed = Embed(color=Color.red(), title=f"A message was deleted by {message.author.name}")
    embed.description = (f"**Original message follows**\n"
                         f"{message.content}\n\n"
                         f"-# Sent at {message.created_at}\n"
                         f"-------\n"
                         f"**User**: {message.author.mention} ({message.author.name})\n"
                         f"**Channel**: {message.channel.mention} ({message.channel.name})\n"
                         f"**Context**: {message.jump_url}\n"
                         f"-------\n"
                         f"*Attachments may follow*")

    for attachment in message.attachments:
        att_embed = Embed(color=Color.greyple(), title=f"{attachment.filename}")

        if (attachment.content_type == "image/png" or attachment.content_type == "image/jpeg"
                or attachment.content_type == "image/webp" or attachment.content_type == "image/gif"):
            att_embed.set_image(url=attachment.url)

        att_embed.description = attachment.url
        attachments.append(att_embed)

    return embed, attachments


def embed_permissions_error(guild: Guild):
    embed = Embed(color=Color.red(), title=f"You don't have permission to use this command!")
    embed.description = f"You need the role <@{guild.configuration['moderator_role']}> to use this command."
    return embed


def embeds_message_edit(before: Message, after: Message):
    b_attachments = []

    b_embed = Embed(color=Color.purple(),
                  title=f"A message was edited by {before.author.name}")
    b_embed.description = (f"**Original message follows**\n"
                         f"{before.content}\n\n"
                         f"-# Sent at {before.created_at}\n"
                         f"-------\n"
                         f"**User**: {before.author.mention} ({before.author.name})\n"
                         f"**Channel**: {before.channel.mention} ({before.channel.name})\n"
                         f"**Context**: {before.jump_url}\n"
                         f"-------\n"
                         f"*Attachments may follow*")

    for attachment in before.attachments:
        att_embed = Embed(color=Color.greyple(), title=f"{attachment.filename}")

        if (attachment.content_type == "image/png" or attachment.content_type == "image/jpeg"
                or attachment.content_type == "image/webp" or attachment.content_type == "image/gif"):
            att_embed.set_image(url=attachment.url)

        att_embed.description = attachment.url
        b_attachments.append(att_embed)


    a_attachments = []

    a_embed = Embed(color=Color.yellow(),
                    title=f"New message")
    a_embed.description = (f"**Edited message follows**\n"
                           f"{after.content}\n\n"
                           f"-------\n"
                           f"*Attachments may follow*")

    for attachment in after.attachments:
        att_embed = Embed(color=Color.greyple(), title=f"{attachment.filename}")

        if (attachment.content_type == "image/png" or attachment.content_type == "image/jpeg"
                or attachment.content_type == "image/webp" or attachment.content_type == "image/gif"):
            att_embed.set_image(url=attachment.url)

        att_embed.description = attachment.url
        a_attachments.append(att_embed)

    return b_embed, b_attachments, a_embed, a_attachments


def message_imprisonment(riddle: Riddle, member: Member):
    return (f"## Welcome to the Dungeon <@!{member.id}> 😏\n"
            f"### Solve the following riddle to get out.\n"
            f"-# Use `/solve <answer>` to solve.\n"
            f"-# Use `/sudoku` to switch to a sudoku if your brain is melting.\n"
            f"> {riddle.text}")


def message_right(riddle: Riddle, is_user_solution: bool = False):
    if riddle.is_sudoku:
        solution_array = [list(map(int, riddle.solution[i:i + 9])) for i in range(0, len(riddle.solution), 9)]
        solution_pretty = display_sudoku(solution_array)

        if is_user_solution:
            return (f"Your solution is also valid! Ours is:\n"
                    f"```{solution_pretty}```\n"
                    f"You have regained your freedom. You'll be freed in 10 seconds.")

        return (f"Good job! The solution was\n"
                f"```{solution_pretty}```\n"
                f"You have regained your freedom. You'll be freed in 10 seconds.")

    return(f"Good job! The answer was `{riddle.solution}`.\n"
           f"You have regained your freedom. You'll be freed in 10 seconds.")


def message_switch_sudoku(riddle: Riddle, member: Member, difficulty: str):
    grid_array = [list(map(int, riddle.text[i:i+9])) for i in range(0, len(riddle.text), 9)]
    grid_pretty = display_sudoku(grid_array)

    return (f"## Damn <@!{member.id}>, you picked the sudoku instead!\n"
                f"-# Use `/solve <answer>` to solve.\n"
                f"-# The solution is to be given in a string format, ***row-by-row***.\n"
                f"```{grid_pretty}```\n"
                f"Difficulty: `{difficulty}`")


def message_wrong(riddle: Riddle):
    if riddle.is_sudoku:
        sudoku_array = [list(map(int, riddle.text[i:i + 9])) for i in range(0, len(riddle.text), 9)]
        sudoku_pretty = display_sudoku(sudoku_array)
        return (f"Wrong! Try again!\n"
                f"```{sudoku_pretty}```")

    return(f"Wrong! Try again!\n"
           f"> {riddle.text}")


def p_embed_kofi(data):
    title = f"{data['type']} ({data['tier_name']})"
    embed = Embed(color=Color.greyple(), title=f"{title}")
    embed.description = f"{data['message']}"

    embed.add_field(name=f"First payment?", value=f"{data['is_first_subscription_payment']}", inline=True)
    embed.add_field(name=f"Amount", value=f"{data['amount']} {data['currency']}", inline=True)
    embed.add_field(name=f"Email", value=f"{data['email']}", inline=False)
    embed.add_field(name=f"Name", value=f"{data['from_name']}", inline=True)
    embed.add_field(name=f"User", value=f"{data['discord_username']}", inline=False)
    embed.add_field(name=f"ID", value=f"<@{data['discord_userid']}>", inline=True)
    embed.add_field(name=f"Transaction", value=f"{data['kofi_transaction_id']}", inline=False)
    embed.add_field(name=f"When", value=f"{data['timestamp']}", inline=False)

    return embed


def message_raid_starting_in(raid: Raid, ping: Role):
    message = (f"## {raid.title} starting in 1 hour!\n"
               f"Don't forget to participate! <@&{ping.id}>\n"
               f"-# Raid#{raid.id} happening on {format_timestamp(datetime.fromisoformat(raid.happens_on).timestamp(), TimestampType.LONG_DATETIME)}.")
    return message

def message_raid_now(raid: Raid, ping: Role):
    message = (f"## {raid.title} now! <@&{ping.id}>\n"
               f"-# Raid#{raid.id}")
    return message


def embed_scheduled_message(message: str, when: datetime):
    title = f"Message scheduled"
    embed = Embed(color=Color.greyple(), title=f"{title}")
    embed.description = f"Your message has been scheduled successfully!"

    embed.add_field(name=f"Message", value=message, inline=False)
    embed.add_field(name=f"When", value=f"{format_timestamp(when.timestamp(), TimestampType.LONG_DATETIME)}", inline=False)

    return embed


def message_scheduled_jobs(interaction: discord.Interaction, jobs: list[Job]):
    body = []
    for job in jobs:
        args = "[" + ",\n".join(map(str, job.args[1:])) + "]"
        body.append([job.id, job.next_run_time, type(job.trigger).__name__, job.args[0], args])

    table = t2a(
        header=["ID", "When", "Trigger", "Function", "Arguments"],
        body=body,
        style=PresetStyle.thin,
        first_col_heading=True
    )

    message = f"# Scheduled jobs\n-# Current server: {interaction.guild.id}\n```\n{table}\n```"
    return message