from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

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

    def banned_to(self) -> Optional[str]:
        if self.ban and self.ban > datetime.now():
            return self.ban.strftime("%d.%m %H:%M")

    @classmethod
    def ban_set(cls, id_: int, time_: int):
        ban_time = datetime.now() + timedelta(minutes=time_)
        cls.update({cls.ban: ban_time}).where(cls.user_id == id_).execute()

    @classmethod
    def notification_get(cls, id_: int) -> bool:
        return cls.get(id_).notifications

    @classmethod
    def notification_set(cls, id_: int, status_: bool):
        cls.update({cls.notifications: int(status_)}).where(cls.user_id == id_).execute()
