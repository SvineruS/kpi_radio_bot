from peewee import SqliteDatabase

from consts.config import PATH_STUFF

PATH_DB = PATH_STUFF / 'db.sqlite'
DB = SqliteDatabase(PATH_DB)
