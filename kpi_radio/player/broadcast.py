# todo выглядит немножко bloated

from __future__ import annotations

from datetime import datetime
from functools import cached_property, cache
from pathlib import Path
from typing import Optional, List, Iterable

from consts import others, config
from utils import DateTime
from .backends import Playlist, PlaylistItem, Backend
from .player_utils import archive, exceptions


class Broadcast(Backend):
    ALL: List[Broadcast] = []

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
    def now(cls) -> Optional[Broadcast]:
        for b in cls.ALL:
            if b.is_now():
                return b
        return None

    @classmethod
    def get_closest(cls) -> Broadcast:
        if br := Broadcast.now():
            return br

        today = DateTime.day_num()
        today_brs = [Broadcast(today, time) for time in others.BROADCAST_TIMES[today]]
        for br in today_brs:
            if not br.is_already_play_today():
                return br
        tomorrow = (today + 1) % 7
        return Broadcast(tomorrow, 0)

    @classmethod
    def is_broadcast_right_now(cls) -> bool:
        return cls.now() is not None

    @property
    def path(self) -> Path:
        path = others.PATHS.ORDERS
        path /= f"D0{self.day + 1}"
        path /= ["0", "10", "12", "13", "15", "5"][self.num]
        return path

    @cached_property
    def name(self) -> str:
        return ', '.join((others.WEEK_DAYS[self.day], others.TIMES[self.num]))

    @property
    def start_time(self) -> datetime:
        return DateTime.strptoday(others.BROADCAST_TIMES[self.day][self.num][0], '%H:%M')

    @property
    def stop_time(self) -> datetime:
        return DateTime.strptoday(others.BROADCAST_TIMES[self.day][self.num][1], '%H:%M')

    def is_today(self) -> bool:
        return self.day == DateTime.day_num()

    def is_now(self) -> bool:
        return self.is_today() and self.start_time < DateTime.now() < self.stop_time

    def is_will_be_play_today(self) -> bool:
        return self.is_today() and self.start_time > DateTime.now()

    def is_already_play_today(self) -> bool:
        return self.is_today() and self.stop_time < DateTime.now()

    #

    def get_local_playlist(self):
        return self._get_local_playlist_provider()(self)

    async def get_playlist(self) -> Playlist:
        if self.is_now():
            return await self.get_player().get_playlist()
        return await self.get_local_playlist().get_playlist()

    async def get_playlist_next(self) -> Playlist:
        # todo а нужно ли...
        pl = await self.get_playlist()
        if self.is_now():
            return pl.trim(DateTime.now(), self.stop_time)
        return pl

    async def get_playback(self):
        if not self.is_now():
            return None
        return await self.get_player().get_playback()

    async def get_free_time(self) -> int:  # seconds
        pl = await self.get_playlist()
        pl = pl.trim(DateTime.now(), self.stop_time).only_orders()
        tracks_duration = pl.duration()
        broadcast_duration = int((self.stop_time - self.start_time).total_seconds())
        return max(0, broadcast_duration - tracks_duration)

    async def add_track(self, track: PlaylistItem, position):
        pl = await self.get_local_playlist().get_playlist()
        if pl.find_by_path(track.path):
            raise exceptions.DuplicateException()
        if await self.get_free_time() < track.duration:
            raise exceptions.NotEnoughSpace()

        track = await self.get_local_playlist().add_track(track, position)
        if self.is_now():
            track = await self.get_player().add_track(track, position)
        return track

    async def remove_track(self, tg_track):
        path = PlaylistItem.from_tg(tg_track, self.path).path
        path.unlink(missing_ok=True)
        await self.get_local_playlist().remove_track(path)
        if self.is_now():
            await self.get_player().remove_track(path)

    async def mark_played(self, path: Path) -> Optional[PlaylistItem]:
        return await self.get_local_playlist().remove_track(path)

    #

    async def play(self):
        if config.PLAYER != 'MOPIDY':  # mopidy specific
            return
        if not self.is_now():
            return

        pl = await self.get_local_playlist().get_playlist()
        if pl:
            await self.get_player().play_playlist(pl)
        else:
            await self.play_from_archive()

    @classmethod
    async def play_from_archive(cls):
        if config.PLAYER != 'MOPIDY':  # mopidy specific
            return
        if not (track := archive.get_random_from_archive()):
            return
        await cls.get_player().add_track(PlaylistItem.from_path(track), -1)
        await cls.get_player().play()

    #

    def __str__(self):
        return self.name

    def __iter__(self) -> Iterable[int]:
        yield self.day
        yield self.num


Broadcast.ALL = [Broadcast(day, num) for day, _num in others.BROADCAST_TIMES.items() for num in _num]
