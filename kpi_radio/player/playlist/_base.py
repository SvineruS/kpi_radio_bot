from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Iterable, Union, List

from consts import others


@dataclass
class PlaylistItem:
    title: str
    path: Path
    duration: int
    time_start: Optional[datetime] = None

    @property
    def is_order(self):
        return str(others.PATHS['orders']) in self.path


class PlaylistBase(list):
    def __init__(self, broadcast, seq=()):
        super().__init__(seq)
        self.broadcast = broadcast

    async def load(self) -> PlaylistBase:
        raise NotImplementedError

    async def add_track(self, track, position=-1) -> None:
        self.insert(position, track)

    async def remove_track(self, file_path) -> Iterable[int]:
        pos = self.find_by_path(file_path)
        for i in pos:
            del self[i]
        return pos

    def find_by_path(self, path: Union[str, Path]) -> List[int]:
        path = str(path)
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