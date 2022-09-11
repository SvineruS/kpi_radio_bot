from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, datetime
from pathlib import Path
from typing import Optional, List, Union, Iterable

from aiogram import types

from consts import others
from player.ether import Ether
from utils import utils


@dataclass
class TrackInfo:
    user_id: int
    user_name: str
    moderation_id: int


@dataclass
class PlaylistItem:
    performer: str
    title: str
    path: Path
    duration: int
    start_time: Optional[datetime] = None
    track_info: Optional[TrackInfo] = None
    ether: Optional[Ether] = None

    @property
    def is_order(self) -> bool:
        return self.track_info is not None

    @property
    def stop_time(self) -> datetime:
        if self.start_time is None:
            raise AttributeError("can't calculate time_stop without time_start")
        return self.start_time + timedelta(seconds=self.duration)

    @classmethod
    def from_tg(cls, tg_track: types.Audio) -> PlaylistItem:
        path = others.PATH_MUSIC / (utils.get_audio_name(tg_track) + '.mp3')
        return PlaylistItem(tg_track.performer, tg_track.title, path, tg_track.duration)

    @classmethod
    def from_path(cls, path: Path):
        return PlaylistItem("", "", path, 0)

    def add_track_info(self, user_id: int, user_name: str, moderation_msg_id: int):
        return self.add_track_info_(TrackInfo(user_id, user_name, moderation_msg_id))

    def add_track_info_(self, track_info: TrackInfo):
        self.track_info = track_info
        return self

    def __str__(self):
        return utils.get_audio_name_(self.performer, self.title)


class Playlist(list):
    def __init__(self, seq=(), time_start=None):
        super().__init__(seq)
        self.time_start = time_start
        self.recalc_time_start()

    def add(self, tracks: Union[PlaylistItem, Playlist]):
        t = tracks if isinstance(tracks, Iterable) else [tracks]
        self.extend(t)
        self.recalc_time_start(-len(t))

    def find_by_path(self, path: Path) -> List[Optional[PlaylistItem]]:
        return [t for t in self if t.path == path] or [None]

    def find_by_user_id(self, user_id: int) -> List[PlaylistItem]:
        return [t for t in self
                if t.track_info and t.track_info.user_id == user_id]

    def trim_by(self, ether: Ether) -> Playlist:
        return self.trim(time_min=ether.start_time, time_max=ether.stop_time)

    def trim(self, time_min: datetime = None, time_max: datetime = None) -> Playlist:
        def trim_():
            for track in self:
                time_start = track.start_time
                if time_min and time_start < time_min:
                    continue
                if time_max and time_start > time_max:
                    break
                yield track
        return self.__class__(list(trim_()), time_start=self.time_start)

    def duration(self) -> int:
        return sum((i.duration for i in self))

    def recalc_time_start(self, from_=0):
        try:
            if from_ == 0:
                raise ValueError
            start_time = self[from_ - 1].stop_time
        except (IndexError, AttributeError, ValueError):
            start_time = self.time_start
            from_ = 0

        for t in self[from_:]:
            t.start_time = start_time
            start_time = t.stop_time
