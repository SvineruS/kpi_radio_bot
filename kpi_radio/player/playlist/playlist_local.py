from __future__ import annotations

from datetime import timedelta, datetime

from consts import config
from ._base import PlaylistBase, PlaylistItem
from ..player_utils import m3u_parser


class PlaylistM3U(PlaylistBase):
    PATH_BASE = config.PATH_STUFF / 'playlists'

    async def load(self) -> PlaylistBase:
        self[:] = []
        duration_sum = timedelta()
        for i in m3u_parser.load(self._get_path()):
            self.append(
                PlaylistItem(title=i.title, path=i.path, duration=i.duration,
                             time_start=self.broadcast.start_time + duration_sum)
            )
            duration_sum += timedelta(seconds=i.duration)
        return self

    async def _save(self):
        m3u_parser.dump(self._get_path(), self)

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
