import calendar
import datetime

from peewee import *

db = SqliteDatabase("data.db")


class BaseModel(Model):
    class Meta:
        database = db


class Guild(BaseModel):
    id = BigIntegerField(unique=True, primary_key=True)
    configuration = TextField(default="{}")
    updated_at = DateTimeField(
        default=calendar.timegm(datetime.datetime.now().timetuple())
    )


class Riddle(BaseModel):
    guild = ForeignKeyField(Guild, backref='riddles')
    user = BigIntegerField()
    text = TextField()
    solution = TextField()
    is_sudoku = BooleanField(default=False)
    updated_at = DateTimeField(
        default=calendar.timegm(datetime.datetime.now().timetuple())
    )


    class Meta:
        primary_key = CompositeKey('guild', 'user')
