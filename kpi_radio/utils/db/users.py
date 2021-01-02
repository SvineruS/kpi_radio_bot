from __future__ import annotations

from datetime import datetime, timedelta

from peewee import Model, BooleanField, BigIntegerField, DateTimeField

from ._connector import DB


class Users(Model):
    user_id = BigIntegerField(primary_key=True)
    ban: datetime = DateTimeField(null=True)
    notifications = BooleanField(default=True)

    @classmethod
    def add(cls, id_):
        cls.insert(user_id=id_).on_conflict_ignore().execute()

    @classmethod
    def get(cls, id_):
        cls.get_or_create(user_id=id_)

    def is_banned(self) -> bool:
        return bool(self.ban and self.ban > datetime.now())

    def banned_to(self):
        return self.ban.strftime("%d.%m %H:%M")

    @classmethod
    def ban_set(cls, id_: int, time_: int):
        ban_time = datetime.now() + timedelta(minutes=time_)
        cls.update(ban=ban_time).where(cls.user_id == id_)

    @classmethod
    def notification_get(cls, id_: int) -> bool:
        return (user := cls.get_by_id(id_)) and user.notifications

    @classmethod
    def notification_set(cls, id_: int, status_: bool):
        cls.update(notifications=status_).where(cls.user_id == id_)

    class Meta:
        database = DB
