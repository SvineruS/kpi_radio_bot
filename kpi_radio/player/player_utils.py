import logging
from datetime import datetime
from functools import cached_property, cache
from random import choice
from typing import Iterable, Optional

from consts import others
from utils import DateTime
from .backends.playlist import PlaylistItem


class Exceptions:
    class RadioExceptions(Exception):
        pass

    class NotEnoughSpaceException(RadioExceptions):
        pass

    class DuplicateException(RadioExceptions):
        pass


class BroadcastGetters:
    @cache
    def __new__(cls, day: int, num: int):
        return super().__new__(cls)

    def __init__(self, day: int, num: int):
        if day not in others.BROADCAST_TIMES:
            raise ValueError("wrong day")
        if num not in others.BROADCAST_TIMES[day]:
            raise ValueError("wrong num")

        self.day: int = day
        self.num: int = num

    @classmethod
    def now(cls):
        for b in cls.ALL:
            if b.is_now():
                return b
        return None

    @classmethod
    def get_closest(cls):
        today = DateTime.day_num()
        for br in (cls(today, time) for time in others.BROADCAST_TIMES[today]):
            if br.is_now() or not br.is_already_play_today():
                return br
        tomorrow = (today + 1) % 7
        return cls(tomorrow, 0)

    @cached_property
    def name(self) -> str:
        return ', '.join((others.WEEK_DAYS[self.day], others.TIMES[self.num]))

    @cached_property
    def start_time(self) -> datetime:
        return DateTime.strptoday(others.BROADCAST_TIMES[self.day][self.num][0], '%H:%M')

    @cached_property
    def stop_time(self) -> datetime:
        return DateTime.strptoday(others.BROADCAST_TIMES[self.day][self.num][1], '%H:%M')

    def is_today(self) -> bool:
        return self.day == DateTime.day_num()

    def is_now(self) -> bool:
        logging.info(str(self))
        return self.is_today() and self.start_time < DateTime.now() < self.stop_time

    def is_will_be_play_today(self) -> bool:
        return self.is_today() and self.start_time > DateTime.now()

    def is_already_play_today(self) -> bool:
        return self.is_today() and self.stop_time < DateTime.now()

    def duration(self, from_now: bool = False):
        s = DateTime.now() if from_now and self.is_now() else self.start_time
        return int((self.stop_time - s).total_seconds())

    def __str__(self):
        return self.name

    def __iter__(self) -> Iterable[int]:
        yield self.day
        yield self.num


def get_random_from_archive() -> Optional[PlaylistItem]:
    tracks = [p for p in others.PATH_MUSIC.iterdir()]
    if tracks:
        return PlaylistItem.from_path(choice(tracks))
    else:
        logging.warning("ARCHIVE is empty")
        return None
