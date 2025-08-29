import calendar
import json

from datetime import datetime, timedelta
from peewee import SqliteDatabase, fn, DoesNotExist
from data.models import Guild, Riddle, Raid, Subscriber


class GuildWrapper():
    id: int
    configuration: dict
    updated_at: datetime


def initialise():
    db = SqliteDatabase("data.db")
    db.create_tables([Guild, Raid, Riddle])


# Start Guild
def create_guild(i_guild: int):
    _ = Guild.get_or_create(id=i_guild)
    guild = Guild.get(Guild.id == i_guild)

    wrap = GuildWrapper()
    wrap.id = guild.id
    wrap.configuration = json.loads(guild.configuration or "{}")
    wrap.updated_at = guild.updated_at

    return wrap


def update_guild(i_guild: int, o_configuration: dict = None):
    _ = Guild.get_or_create(id=i_guild)
    guild = Guild.get(Guild.id == i_guild)

    o_stored: dict = json.loads(guild.configuration or "{}")

    if o_configuration is not None:
        o_final = o_stored | o_configuration
        guild.configuration = json.dumps(o_final)

    guild.save()

    wrap = GuildWrapper()
    wrap.id = guild.id
    wrap.configuration = json.loads(guild.configuration)
    wrap.updated_at = guild.updated_at

    return wrap
# End Guild


# Start Raid
def create_raid(i_guild: int, i_user: int, s_title: str, s_description: str, d_apply_by: datetime, d_happens_on: datetime):
    _ = Raid.get_or_create(guild=i_guild, organiser=i_user, title=s_title, description=s_description, apply_by=d_apply_by, happens_on=d_happens_on)
    raid = Raid.get(Raid.guild == i_guild, Raid.organiser == i_user, Raid.happens_on == d_happens_on)
    return raid


def read_raid(i_raid: int):
    raid = Raid.get(Raid.id == i_raid)
    return raid


def update_raid(i_raid: int, s_title: str = None, s_description: str = None, o_participants: dict = None, d_apply_by: datetime = None, d_happens_on: datetime = None):
    raid = read_raid(i_raid)

    if s_title is not None:
        raid.title = s_title
    if s_description is not None:
        raid.description = s_description
    if o_participants is not None:
        raid.participants = json.dumps(o_participants)
    if d_apply_by is not None:
        raid.apply_by = d_apply_by
    if d_happens_on is not None:
        raid.happens_on = d_happens_on

    raid.save()


def delete_raid(i_raid: int):
    raid = read_raid(i_raid)
    raid.delete_instance()


def get_raid_leader(i_raid: int):
    raid = read_raid(i_raid)
    participants: dict = json.loads(raid.participants or "{}")

    try:
        return participants["leader"]
    except KeyError:
        return None


def set_raid_leader(i_raid: int, leader: int):
    raid = read_raid(i_raid)
    participants: dict = json.loads(raid.participants or "{}")
    participants["leader"] = leader

    raid.participants = json.dumps(participants)
    raid.save()


def get_raid_supports(i_raid: int):
    raid = read_raid(i_raid)
    participants: dict = json.loads(raid.participants or "{}")

    try:
        return participants["supports"]
    except KeyError:
        return []


def set_raid_supports(i_raid: int, supports: list[int]):
    raid = read_raid(i_raid)
    participants: dict = json.loads(raid.participants or "{}")

    try:
        participants["supports"] = list(set(participants["supports"]) ^ set(supports))
    except KeyError:
        participants["supports"] = supports

    raid.participants = json.dumps(participants)
    raid.save()
# End Raid


# Start Riddle
def create_riddle(i_guild: int, i_user: int, s_text: str, s_solution: str):
    _ = Riddle.get_or_create(guild=i_guild, user=i_user, text=s_text, solution=s_solution)
    riddle = Riddle.get(Riddle.guild == i_guild, Riddle.user == i_user)
    return riddle


def read_riddle(i_guild: int, i_user: int):
    riddle = Riddle.get(Riddle.guild == i_guild, Riddle.user == i_user)
    return riddle


def update_riddle(i_guild: int, i_user: int, s_text: str = None, s_solution: str = None, b_sudoku: bool = False):
    riddle = read_riddle(i_guild, i_user)

    if s_text is not None:
        riddle.text = s_text

    if s_solution is not None:
        riddle.solution = s_solution

    riddle.is_sudoku = b_sudoku

    riddle.save()
    return riddle


def delete_riddle(i_guild: int, i_user: int):
    riddle = read_riddle(i_guild, i_user)
    riddle.delete_instance()
# End Riddle


# Start Licence
def create_subscriber(i_guild: int, d_since: datetime, d_until: datetime):
    _ = Subscriber.get_or_create(guild=i_guild, since=d_since, until=d_until)
    subscriber = Subscriber.get(Subscriber.guild == i_guild)
    return subscriber


def read_subscriber(i_guild: int):
    subscriber = Subscriber.get(Subscriber.guild == i_guild)
    return subscriber


def update_subscriber(i_guild: int, d_since: datetime = None, d_until: datetime = None):
    subscriber = read_subscriber(i_guild)

    if d_since is not None:
        subscriber.since = d_since

    if d_until is not None:
        subscriber.until = d_until

    subscriber.save()
    return subscriber


def delete_subscriber(i_guild: int):
    subscriber = read_subscriber(i_guild)
    subscriber.delete_instance()
# End Licence