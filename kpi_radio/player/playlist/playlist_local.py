from __future__ import annotations

from datetime import datetime
from pathlib import Path

from consts import config
from ._base import PlaylistBase, PlaylistItem
from ..player_utils import m3u_parser


class PlaylistM3U(PlaylistBase):
    PATH_BASE = config.PATH_STUFF / 'playlists'

    async def load(self) -> PlaylistBase:
        self[:] = []
        for i in m3u_parser.load(self.get_path()):
            self.append(
                PlaylistItem(title=i.title, path=i.path, duration=i.duration, start_time=self._get_start_time())
            )
        return self

    async def _save(self):
        m3u_parser.dump(self.get_path(), self)

    async def add_track(self, track: PlaylistItem, position: int = -1):
        await super().add_track(track, position)
        await self._save()

    async def remove_track(self, file_path: Path):
        await super().remove_track(file_path)
        await self._save()

    def trim(self, time_min: datetime = None, time_max: datetime = None):
        return self

    def get_path(self):
        return self.PATH_BASE / f"{self.broadcast.day}-{self.broadcast.num}"
