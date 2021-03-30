from peewee import SqliteDatabase, Model

from consts.config import PATH_STUFF

PATH_DB = PATH_STUFF / 'db.sqlite'
DB = SqliteDatabase(PATH_DB)


class BaseModel(Model):
    class Meta:
        database = DB
