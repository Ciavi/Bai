import calendar

from datetime import datetime, timedelta
from peewee import SqliteDatabase, fn, DoesNotExist
from data.models import Guild, Riddle


def initialise():
    db = SqliteDatabase("data.db")
    db.create_tables([Guild, Riddle])


# Start Guild
def create_guild(i_guild: int):
    _ = Guild.get_or_create(id=i_guild)
    guild = Guild.get(Guild.id == i_guild)
    return guild


def update_guild(i_guild: int, i_moderator: int = None, i_inmate: int = None, i_jail: int = None):
    guild = create_guild(i_guild)

    if i_moderator is not None:
        guild.moderator_role = i_moderator

    if i_inmate is not None:
        guild.inmate_role = i_inmate

    if i_jail is not None:
        guild.jail_channel = i_jail

    guild.save()
    return guild
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

