from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Iterable, List

from aiogram import types

from utils.utils import get_by
from consts import others


@dataclass
class PlaylistItem:
    title: str
    path: Path
    duration: int
    time_start: Optional[datetime] = None

    @property
    def is_order(self) -> bool:
        return others.PATHS['orders'] in self.path.parents

    @property
    def time_stop(self) -> datetime:
        if self.time_start is None:
            raise Exception("can't calculate time_stop without time_start")
        return self.time_start + timedelta(seconds=self.duration)

    @classmethod
    def from_tg(cls, tg_track: types.Audio, path_base: Path) -> PlaylistItem:
        name = get_by.get_audio_name(tg_track)
        return PlaylistItem(name, path_base / (name + '.mp3'), tg_track.duration)


class PlaylistBase(list):
    def __init__(self, broadcast, seq=()):
        super().__init__(seq)
        self.broadcast = broadcast

    async def load(self) -> PlaylistBase:
        raise NotImplementedError

    async def add_track(self, track: PlaylistItem, position: int = -1) -> PlaylistItem:
        track.time_start = self._get_start_time(position-1)
        self.insert(position, track)
        return self[position]

    async def remove_track(self, file_path: Path) -> Iterable[int]:
        pos = self.find_by_path(file_path)[0]
        track = self[pos]
        self.pop(pos)
        return pos, track

    def find_by_path(self, path: Path) -> List[int]:
        return [i for i, t in enumerate(self) if t.path == path]

    def only_next(self) -> Iterable[PlaylistItem]:
        return self.trim(datetime.now())

    def only_orders(self):
        return self.__class__(self.broadcast, [i for i in self if i.is_order])

    def trim(self, time_min: datetime = None, time_max: datetime = None) -> PlaylistBase:
        def trim_():
            for track in self:
                time_start = track.time_start
                if time_min and time_start < time_min:
                    continue
                if time_max and time_start > time_max:
                    break
                yield track
        return self.__class__(self.broadcast, list(trim_()))

    def duration(self) -> int:
        return sum((i.duration for i in self))

    def _get_start_time(self, index: int = -1):
        try:
            return self[index].stop_time
        except KeyError:
            return self.broadcast.start_time
