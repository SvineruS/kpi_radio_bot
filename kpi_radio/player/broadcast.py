from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional, List

import utils.get_by
from consts import others
from utils.lru import lru
from .player_utils import files, radioboss, exceptions
from .playlist import Playlist, PlaylistItem, PlaylistBase


class Broadcast:
    ALL: List[Broadcast] = []

    @lru()
    def __new__(cls, day: int, num: int):
        return super().__new__(cls)

    def __init__(self, day: int, num: int):
        if day not in others.BROADCAST_TIMES_:
            raise Exception("wrong day")
        if num not in others.BROADCAST_TIMES_[day]:
            raise Exception("wrong num")

        self.day: int = day
        self.num: int = num

    @classmethod
    def now(cls):
        for b in cls.ALL:
            if b.is_now():
                return b

    @classmethod
    def get_closest(cls):
        if br := Broadcast.now():
            return br

        today = datetime.today().weekday()
        today_brs = [Broadcast(today, time) for time in others.BROADCAST_TIMES_[today]]
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
        path = others.PATHS['orders']
        path /= f"D0{self.day + 1}"
        path /= ["0", "10", "12", "13", "15", "5"][self.num]
        return path

    @property
    def name(self) -> str:
        return ', '.join((others.WEEK_DAYS[self.day], others.TIMES[self.num]))

    @property
    def start_time(self) -> datetime:
        return utils.get_by.time_to_datetime(others.BROADCAST_TIMES_[self.day][self.num][0])

    @property
    def stop_time(self) -> datetime:
        return utils.get_by.time_to_datetime(others.BROADCAST_TIMES_[self.day][self.num][1])

    def is_today(self) -> bool:
        return self.day == datetime.now().weekday()

    def is_now(self) -> bool:
        return self.is_today() and self.start_time < datetime.now() < self.stop_time

    def is_will_be_play_today(self) -> bool:
        return self.is_today() and self.start_time > datetime.now()

    def is_already_play_today(self) -> bool:
        return self.is_today() and self.stop_time < datetime.now()

    async def playlist(self) -> PlaylistBase:
        return await Playlist(self).load()

    async def get_playlist_next(self) -> PlaylistBase:
        pl = await self.playlist()
        if self.is_now():
            return pl.trim(datetime.now(), self.stop_time)
        return pl

    async def get_prev_now_next(self):
        if not self.is_now():
            return None
        return await Playlist.get_prev_now_next()

    async def get_free_time(self) -> int:  # seconds
        pl = await self.playlist()
        pl = pl.trim(datetime.now(), self.stop_time).only_orders()
        duration = pl.duration()
        return max(0, (self.stop_time - self.start_time).total_seconds() - duration)

    async def add_track(self, tg_track, metadata=None, position=-1):
        pl = await self.playlist()
        n_ = utils.get_by.get_audio_name(tg_track)
        track = PlaylistItem(n_, self._get_audio_path(n_), tg_track.duration)
        if pl.find_by_path(track.path):
            raise exceptions.DuplicateException()
        if await self.get_free_time() < track.duration:
            raise exceptions.NotEnoughSpace
        await files.download_audio(tg_track, track.path)
        await radioboss.write_track_additional_info(track.path, *metadata)
        if self.is_now():
            position = await self._get_new_order_pos()
        await pl.add_track(track, position)
        # ебать костыли
        track = (await self.playlist()).find_by_path(track.path)[0]
        return track

    async def remove_track(self, tg_track):
        path = self._get_audio_path(utils.get_by.get_audio_name(tg_track))
        files.delete_file(path)
        pl = await self.playlist()
        await pl.remove_track(path)

    #

    async def _get_new_order_pos(self) -> Optional[PlaylistItem]:
        if not self.is_now():
            return None
        pl = await self.get_playlist_next()
        return _get_new_order_pos(pl)

    def _get_audio_path(self, audio_name: str) -> Path:
        return self.path / (audio_name + '.mp3')

    def __str__(self):
        return self.name

    def __iter__(self) -> int:
        yield self.day
        yield self.num


Broadcast.ALL = [Broadcast(day, num) for day, _num in others.BROADCAST_TIMES_.items() for num in _num]

#


def _get_new_order_pos(playlist_: PlaylistBase) -> Optional[int]:
    if not playlist_ or playlist_[-1].is_order:  # если последний трек, что успеет проиграть, это заказ - вернем None
        return None

    for i, track in reversed(list(enumerate(playlist_))):
        if track.is_order:  # т.к. заказы всегда в начале плейлиста, то нужен трек, следующий после последнего заказа
            return i + 1
    return 0  # если нету заказов - будет первым
