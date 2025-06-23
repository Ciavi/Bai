import calendar
import json

from datetime import datetime, timedelta
from peewee import SqliteDatabase, fn, DoesNotExist
from data.models import Guild, Riddle


class GuildWrapper():
    id: int
    configuration: dict
    updated_at: datetime


def initialise():
    db = SqliteDatabase("data.db")
    db.create_tables([Guild, Riddle])


# Start Guild
def create_guild(i_guild: int):
    _ = Guild.get_or_create(id=i_guild)
    guild = Guild.get(Guild.id == i_guild)

    wrap = GuildWrapper()
    wrap.id = guild.id
    wrap.configuration = json.loads(guild.configuration)
    wrap.updated_at = guild.updated_at

    return wrap


def update_guild(i_guild: int, o_configuration: dict = None):
    _ = Guild.get_or_create(id=i_guild)
    guild = Guild.get(Guild.id == i_guild)

    o_stored: dict = json.loads(guild.configuration)

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

