from __future__ import annotations

from datetime import datetime
from functools import cached_property, cache
from typing import Iterable, List, Optional

from consts import others
from utils import DateTime


class Ether:
    ALL: List[Ether] = []

    # special ether for orders accepted with "NOW" button
    # will be play at any time if not empty
    OUT_OF_QUEUE: Ether

    def __new__(cls, day: int, num: int):
        return super().__new__(cls)

    def __init__(self, day: int, num: int):
        if day not in others.ETHER_TIMES:
            raise ValueError("wrong day")
        if num not in others.ETHER_TIMES[day]:
            raise ValueError("wrong num")

        self.day: int = day
        self.num: int = num

    @classmethod
    def now(cls) -> Optional[Ether]:
        for b in cls.ALL:
            if b.is_now():
                return b
        return None

    @classmethod
    def get_closest(cls) -> Ether:
        today = DateTime.day_num()
        for br in (cls(today, time) for time in others.ETHER_TIMES[today]):
            if br.is_now() or not br.is_already_play_today():
                return br
        tomorrow = (today + 1) % 7
        return cls(tomorrow, 0)

    @property
    def name(self) -> str:
        return ', '.join((others.WEEK_DAYS[self.day], others.ETHER_NAMES[self.num]))

    @property
    def start_time(self) -> datetime:
        return DateTime.strptoday(others.ETHER_TIMES[self.day][self.num][0], '%H:%M')

    @property
    def stop_time(self) -> datetime:
        return DateTime.strptoday(others.ETHER_TIMES[self.day][self.num][1], '%H:%M')

    def is_today(self) -> bool:
        return self.day == DateTime.day_num()

    def is_now(self) -> bool:
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


Ether.ALL = [Ether(day, num) for day, _num in others.ETHER_TIMES.items() for num in _num]

Ether.OUT_OF_QUEUE = Ether(0, 0)
Ether.OUT_OF_QUEUE.day = -1
