from __future__ import annotations

from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

from peewee import IntegerField, BigIntegerField, CharField, DecimalField, CompositeKey, SmallIntegerField, fn

from ._connector import BaseModel

if TYPE_CHECKING:
    from player import PlaylistItem, Ether


class Tracklist(BaseModel):
    track_path = CharField(max_length=750)
    track_performer = CharField(max_length=200, null=True)
    track_title = CharField(max_length=200)
    track_duration = IntegerField()

    info_user_id = BigIntegerField()
    info_user_name = CharField(max_length=100)
    info_message_id = BigIntegerField()
    ether_day = SmallIntegerField()
    ether_num = SmallIntegerField()

    position = IntegerField()

    @classmethod
    def add(cls, track: PlaylistItem, ether: Ether):
        assert track.track_info is not None, "Local playlist need track info!"
        position = cls.select(fn.Max(cls.position)).where(*_e2cmp(ether)).scalar() or 0

        cls.insert(
            track_path=track.path.name, track_performer=track.performer,
            track_title=track.title, track_duration=track.duration,
            info_user_id=track.track_info.user_id, info_user_name=track.track_info.user_name,
            info_message_id=track.track_info.moderation_id,
            ether_day=ether.day, ether_num=ether.num, position=position+1
        ).on_conflict_replace().execute()

    @classmethod
    def get_by_ether(cls, ether: Ether):
        return cls.select().where(*_e2cmp(ether)).order_by(cls.position.asc())

    @classmethod
    def get_track_by_path(cls, ether: Ether, path: Path) -> Optional[Tracklist]:
        return cls.select().where(*_e2cmp(ether), cls.track_path == path.name).first()

    @classmethod
    def remove_track(cls, ether: Ether, path: Path) -> Optional[Tracklist]:
        if track := cls.get_track_by_path(ether, path):
            track.delete_instance()
            return track
        return None

    @classmethod
    def clear_ether(cls, ether: Ether):
        cls.delete().where(*_e2cmp(ether))

    class Meta:
        indexes = (  # связка уникальных полей
            (('ether_day', 'ether_num', 'track_path'), True),
            (('ether_day', 'ether_num', 'position'), True),
        )
        primary_key = CompositeKey('ether_day', 'ether_num', 'track_path')


def _e2cmp(e: Ether):
    return Tracklist.ether_day == e.day, Tracklist.ether_num == e.num
