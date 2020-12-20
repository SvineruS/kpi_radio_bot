from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Union, Iterable, Iterator

from consts import others, config
from utils.get_by import time_to_datetime
from . import radioboss, _m3u_parser


class PlaylistItem:
    def __init__(self, title, path, duration, time_start=None):
        self.title = title
        self.path = path
        self.time_start = time_start
        self.duration = duration

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

    def find_by_path(self, path: Union[str, Path]) -> Iterator[int, None]:
        path = str(path)
        return (i for i, t in enumerate(self) if t.path == path)

    def only_next(self) -> Iterable[PlaylistItem]:
        return self.trim(datetime.now())

    def only_orders(self):
        return Playlist(self.broadcast, [i for i in self if i.is_order])

    def trim(self, time_min: datetime = None, time_max: datetime = None):
        def trim_():
            for track in self:
                time_start = track.time_start
                if time_min and time_start < time_min:
                    continue
                if time_max and time_start > time_max:
                    break
                yield track
        return Playlist(self.broadcast, list(trim_()))

    def duration(self) -> int:
        return sum((i.duration for i in self))


class PlaylistM3U(PlaylistBase):
    PATH_BASE = config.PATH_STUFF / 'playlists'

    async def load(self):
        self[:] = []
        duration_sum = timedelta()
        for i in _m3u_parser.load(self._get_path()):
            self.append(
                PlaylistItem(title=i.title, path=i.path, duration=i.duration,
                             time_start=self.broadcast.start_time + duration_sum)
            )
            duration_sum += timedelta(seconds=i.duration)
        return self

    async def _save(self):
        _m3u_parser.dump(self._get_path(), self)

    async def add_track(self, track, position=-1):
        await super().add_track(track, position)
        await self._save()

    async def remove_track(self, file_path):
        await super().remove_track(file_path)
        await self._save()

    def trim(self, time_min: datetime = None, time_max: datetime = None):
        return self

    def _get_path(self):
        return self.PATH_BASE / f"{self.broadcast.day}-{self.broadcast.num}"


class PlaylistRadioboss(PlaylistBase):
    async def load(self):
        self[:] = [
            PlaylistItem(
               title=track['@CASTTITLE'],
               time_start=time_to_datetime(datetime.strptime(track['@STARTTIME'], '%H:%M:%S').time()),  # set today
               path=track['@FILENAME'],
               duration=(datetime.strptime(track['@STARTTIME'], '%H:%M:%S') - datetime(1900, 1, 1)).total_seconds()
            )
            for track in (await radioboss.getplaylist2())['TRACK']
            if track['@STARTTIME']  # если STARTTIME == "" - это не песня (либо она стартанет через >=сутки)
        ]
        return self

    @staticmethod
    async def get_prev_now_next():
        playback = await radioboss.playbackinfo()
        if not playback or playback['Playback']['@state'] == 'stop':
            return None

        result = [''] * 3
        for i, k in enumerate(('PrevTrack', 'CurrentTrack', 'NextTrack')):
            title = playback[k]['TRACK']['@CASTTITLE']
            if "setvol" not in title:
                result[i] = title
        return result

    async def add_track(self, track, position=-1):
        await super().add_track(track, position)
        await radioboss.inserttrack(track.path, -2 if position == 0 else position)

    async def remove_track(self, file_path):
        pos = await super().remove_track(file_path)
        await radioboss.delete(pos)


class Playlist(PlaylistM3U, PlaylistRadioboss):
    def __new__(cls, broadcast, seq=()) -> PlaylistBase:
        if broadcast.is_now():
            return PlaylistRadioboss(broadcast, seq)
        else:
            return PlaylistM3U(broadcast, seq)
