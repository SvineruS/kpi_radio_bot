from __future__ import annotations

from datetime import datetime, timedelta

from peewee import BigIntegerField, CharField, DateTimeField

from consts.btns_text import STATUS
from ._connector import BaseModel


class Stats(BaseModel):
    message_id = BigIntegerField(primary_key=True)
    moderator_id = BigIntegerField()
    user_id = BigIntegerField()
    track_title = CharField(max_length=500)
    moderation_status = CharField(max_length=20)
    date = DateTimeField()

    @classmethod
    def add(cls, message_id: int, moderator_id: int, user_id: int, track_title: str,
            moderation_status: STATUS, date: datetime):
        cls.insert(
            message_id=message_id,
            moderator_id=moderator_id,
            user_id=user_id,
            track_title=track_title,
            moderation_status=moderation_status,
            date=date
        ).on_conflict_replace().execute()

    @classmethod
    def get_last_n_days(cls, days):
        return cls.select().where(cls.date >= (datetime.today() - timedelta(days=days)))

    def is_own(self):
        return self.user_id == self.moderator_id
