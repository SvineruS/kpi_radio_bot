from __future__ import annotations

from datetime import datetime
from functools import cached_property, cache
from pathlib import Path
from typing import Optional, List, Iterable

from consts import others, config
from utils import DateTime
from .backends import Player, LocalPlaylist, Playlist, PlaylistItem, IPlaylistProvider
from .player_utils import files, exceptions, TrackInfo


class Broadcast:
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

    async def playlist(self) -> Playlist:
        return await self.get_playlist_provider().get_playlist()

    def get_playlist_provider(self) -> IPlaylistProvider:
        return Player if self.is_now() else LocalPlaylist

    async def get_playlist_next(self) -> Playlist:
        pl = await self.playlist()
        if self.is_now():
            return pl.trim(DateTime.now(), self.stop_time)
        return pl

    async def get_playback(self):
        if not self.is_now():
            return None
        return await Player.get_playback()

    async def get_free_time(self) -> int:  # seconds
        pl = await self.playlist()
        pl = pl.trim(DateTime.now(), self.stop_time).only_orders()
        tracks_duration = pl.duration()
        broadcast_duration = int((self.stop_time - self.start_time).total_seconds())
        return max(0, broadcast_duration - tracks_duration)

    async def add_track(self, tg_track, metadata, position):
        track = PlaylistItem.from_tg(tg_track, self.path)
        if (await self.playlist()).find_by_path(track.path):
            raise exceptions.DuplicateException()
        if await self.get_free_time() < track.duration:
            raise exceptions.NotEnoughSpace
        await files.download_audio(tg_track, track.path)
        if metadata:
            await TrackInfo(*metadata).write(track.path)
        track = await self.get_playlist_provider().add_track(track, position)
        print(track)
        return track

    async def remove_track(self, tg_track):
        path = PlaylistItem.from_tg(tg_track, self.path).path
        files.delete_file(path)
        await self.get_playlist_provider().remove_track(path)

    #

    async def play(self):
        if config.PLAYER != 'MOPIDY':  # mopidy specific
            return
        if not self.is_now():
            return
        playlist_path = LocalPlaylist(self).get_path()
        res = await Player.play_playlist(playlist_path)
        if not res:
            await self.play_from_archive()

    @staticmethod
    async def play_from_archive():
        if config.PLAYER != 'MOPIDY':  # mopidy specific
            return
        if not (track := files.get_random_from_archive()):
            return
        await Player.add_track(PlaylistItem.from_path(track), -1)
        await Player.play()

    #

    def __str__(self):
        return self.name

    def __iter__(self) -> Iterable[int]:
        yield self.day
        yield self.num


Broadcast.ALL = [Broadcast(day, num) for day, _num in others.BROADCAST_TIMES.items() for num in _num]

#
