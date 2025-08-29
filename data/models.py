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


class Raid(BaseModel):
    id = BigIntegerField(unique=True, primary_key=True)
    guild = BigIntegerField()
    organiser = BigIntegerField()
    title = TextField()
    description = TextField()
    participants = TextField(default="{}")
    apply_by = DateTimeField()
    happens_on = DateTimeField()
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


class Subscribers(BaseModel):
    guild = ForeignKeyField(Guild, backref='subscribers')
    since = DateTimeField()
    until = DateTimeField()
    ontime = BooleanField(default=True)
    updated_at = DateTimeField(
        default=calendar.timegm(datetime.datetime.now().timetuple())
    )


    class Meta:
        primary_key = CompositeKey('guild', 'user')
