from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from peewee import Model, IntegerField, BigIntegerField, CharField, DecimalField, CompositeKey

from ._connector import DB


_POSITION_EXTRA_SPACE = 5


class Tracklist(Model):
    track_path = CharField(max_length=750)
    track_performer = CharField(max_length=200)
    track_title = CharField(max_length=200)
    track_duration = IntegerField()

    info_user_id = BigIntegerField()
    info_user_name = CharField(max_length=100)
    info_message_id = BigIntegerField()

    broadcast_day = DecimalField(max_digits=1)
    broadcast_num = DecimalField(max_digits=1)

    position = DecimalField(max_digits=5, decimal_places=_POSITION_EXTRA_SPACE)

    @classmethod
    def add(cls, track_position, track_path, track_performer, track_title, track_duration,
            info_user_id, info_user_name, info_message_id,
            broadcast_day, broadcast_num
            ):

        def _get_available_position(pos: Optional[int] = None) -> Decimal:
            """Кароч позиция это Decimal, где целая часть - то, что приходит из вне, а
            дробная часть - меняется для устранения "коллизий" оставляя порядок"""
            if pos is None:
                new_pos = cls.select(cls.position) \
                    .where(cls.broadcast_num == broadcast_num, cls.broadcast_day == broadcast_day)\
                    .order_by(cls.position.desc()).limit(1)
                if new_pos:
                    return new_pos[0]
                return Decimal(0)
            else:
                new_pos = cls.select(cls.position) \
                    .where(cls.broadcast_num == broadcast_num, cls.broadcast_day == broadcast_day,
                           cls.position.between(pos, pos + 1)) \
                    .order_by(cls.position.asc()).limit(1)
                if new_pos:
                    return new_pos - 10 ** (_POSITION_EXTRA_SPACE * -1)
                return Decimal(pos)

        cls.insert(
            track_position=_get_available_position(track_position),
            track_path=track_path, track_performer=track_performer,
            track_title=track_title, track_duration=track_duration,
            info_user_id=info_user_id, info_user_name=info_user_name, info_message_id=info_message_id,
            broadcast_day=broadcast_day, broadcast_num=broadcast_num
        ).on_conflict_replace().execute()

    @classmethod
    def get_by_broadcast(cls, day, num) -> List[Tracklist]:
        return cls.select().where(cls.broadcast_num == day, cls.broadcast_num == num).order_by(cls.position.asc())

    @classmethod
    def get_track_by_path(cls, day, num, path) -> Optional[Tracklist]:
        res = cls.select().where(cls.broadcast_num == day, cls.broadcast_num == num, cls.track_path == path)
        return res[0] if res else None

    @classmethod
    def remove_track(cls, day, num, path) -> Optional[Tracklist]:
        if track := cls.get_track_by_path(day, num, path):
            track.delete_instance()
            return track
        return None

    @classmethod
    def remove_tracks(cls, day, num):
        cls.delete().where(cls.broadcast_num == day, cls.broadcast_num == num)

    class Meta:
        indexes = (  # связка уникальных полей
            (('broadcast_day', 'broadcast_num', 'track_path'), True),
            (('broadcast_day', 'broadcast_num', 'position'), True),
        )
        primary_key = CompositeKey('broadcast_day', 'broadcast_num', 'track_path')
        database = DB
