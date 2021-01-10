from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, datetime
from pathlib import Path
from typing import Optional, Iterable, List

from aiogram import types

from consts import others
from utils import DateTime, utils


@dataclass
class PlaylistItem:
    performer: str
    title: str
    path: Path
    duration: int
    start_time: Optional[datetime] = None

    @property
    def is_order(self) -> bool:
        return others.PATHS.ORDERS in self.path.parents

    @property
    def stop_time(self) -> datetime:
        if self.start_time is None:
            raise AttributeError("can't calculate time_stop without time_start")
        return self.start_time + timedelta(seconds=self.duration)

    @classmethod
    def from_tg(cls, tg_track: types.Audio, path_base: Path) -> PlaylistItem:
        path = path_base / (utils.get_audio_name(tg_track) + '.mp3')
        return PlaylistItem(tg_track.performer, tg_track.title, path, tg_track.duration)

    @classmethod
    def from_path(cls, path: Path):
        return PlaylistItem("", "", path, 0)

    def __str__(self):
        return f"{self.performer} - {self.title}"


class Playlist(list):
    def __init__(self, seq=()):
        super().__init__(seq)

    def find_by_path(self, path: Path) -> List[int]:
        return [i for i, t in enumerate(self) if t.path == path]

    def only_next(self) -> Iterable[PlaylistItem]:
        return self.trim(DateTime.now())

    def only_orders(self):
        return self.__class__([i for i in self if i.is_order])

    def trim(self, time_min: datetime = None, time_max: datetime = None) -> Playlist:
        def trim_():
            for track in self:
                time_start = track.start_time
                if time_min and time_start < time_min:
                    continue
                if time_max and time_start > time_max:
                    break
                yield track
        return self.__class__(list(trim_()))

    def duration(self) -> int:
        return sum((i.duration for i in self))
