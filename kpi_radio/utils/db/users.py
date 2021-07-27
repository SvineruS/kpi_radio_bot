from __future__ import annotations

from datetime import datetime, timedelta

from peewee import BooleanField, BigIntegerField, DateTimeField

from ._connector import BaseModel


class Users(BaseModel):
    user_id = BigIntegerField(primary_key=True)
    ban: datetime = DateTimeField(null=True)
    notifications = BooleanField(default=True)

    @classmethod
    def add(cls, id_):
        cls.insert(user_id=id_).on_conflict_ignore().execute()

    @classmethod
    def get(cls, id_):
        user, _ = cls.get_or_create(user_id=id_)
        return user

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
