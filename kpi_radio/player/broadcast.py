from __future__ import annotations

import logging
from datetime import datetime
from functools import cached_property, cache
from pathlib import Path
from typing import Iterable, Optional, List

from consts import others, config
from utils import DateTime
from .backends import Playlist, PlaylistItem, DBPlaylistProvider, PlayerMopidy
from .player_utils import Exceptions, get_random_from_archive


class Broadcast:
    ALL: List[Broadcast] = []
    player = PlayerMopidy(url=config.MOPIDY_URL)

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
        return self.is_today() and self.start_time < DateTime.now() < self.stop_time

    def is_will_be_play_today(self) -> bool:
        return self.is_today() and self.start_time > DateTime.now()

    def is_already_play_today(self) -> bool:
        return self.is_today() and self.stop_time < DateTime.now()

    def duration(self, from_now: bool = False):
        s = DateTime.now() if from_now and self.is_now() else self.start_time
        return int((self.stop_time - s).total_seconds())

    #

    @property
    def playlist(self) -> DBPlaylistProvider:
        return DBPlaylistProvider(self)

    async def get_playlist_next(self) -> Playlist:
        pl = await self.playlist.get_playlist()
        if self.is_now():
            return pl.trim(time_max=self.stop_time)
        return pl

    async def get_playback(self) -> Optional[List[PlaylistItem]]:
        return [
            await self.player.get_prev_track(),
            await self.player.get_current_track(),
            await self.playlist.get_next_track(),
        ] if self.is_now() else None

    async def get_free_time(self) -> int:  # seconds
        pl = (await self.playlist.get_playlist()).trim(time_max=self.stop_time)
        return max(0, self.duration(from_now=True) - pl.duration())

    async def add_track(self, track: PlaylistItem, position, audio) -> PlaylistItem:
        pl = await self.playlist.get_playlist()
        if pl.find_by_path(track.path):
            raise Exceptions.DuplicateException()
        if await self.get_free_time() < track.duration:
            raise Exceptions.NotEnoughSpaceException()

        if not track.path.exists():
            await audio.download(track.path)

        return await self.playlist.add_track(track, position)

    async def remove_track(self, track: PlaylistItem, remove_file=True):
        if remove_file:
            track.path.unlink(missing_ok=True)
        await self.playlist.remove_track(track.path)

    async def mark_played(self, path: Path) -> Optional[PlaylistItem]:
        return await self.playlist.remove_track(path)

    @classmethod
    async def play(cls, broadcast=None):
        track = (await broadcast.playlist.get_next_track() if broadcast else None) or get_random_from_archive()
        if not track:
            return logging.warning('No tracks to play')

        await cls.player.add_track(track)
        if await cls.player.play():
            return logging.info("Play " + str(track.path))

        logging.error("Failed to play " + str(track.path))
        if broadcast:
            await broadcast.remove_track(track, remove_file=False)
        await cls.play()

    def __str__(self):
        return self.name

    def __iter__(self) -> Iterable[int]:
        yield self.day
        yield self.num


Broadcast.ALL = [Broadcast(day, num) for day, _num in others.BROADCAST_TIMES.items() for num in _num]
