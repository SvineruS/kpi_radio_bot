from __future__ import annotations

from pathlib import Path
from typing import List

from consts import config
from utils import DateTime
from . import _m3u_parser
from .._base import LocalPlaylistProviderBase, Playlist, PlaylistItem


def _get_start_time(prev_item: PlaylistItem = None):
    if prev_item:
        return prev_item.stop_time
    return DateTime.now()


class M3UPlaylistProvider(LocalPlaylistProviderBase):
    PATH_BASE = config.PATH_STUFF / 'playlists'

    async def get_playlist(self) -> Playlist:
        pl: List[PlaylistItem] = []
        for i in _m3u_parser.load(self.get_path()):
            pl.append(PlaylistItem(
                performer=i.performer,
                title=i.title,
                path=i.path,
                duration=i.duration,
                start_time=_get_start_time(pl[-1] if pl else None)
            ))
        return Playlist(pl)

    async def add_track(self, track: PlaylistItem, position: int) -> PlaylistItem:
        if position == -2:
            position = 0
        pl = await self.get_playlist()
        pl.insert(position, track)
        await self._save(pl)
        return pl[position]

    async def remove_track(self, track_path: Path):
        pl = await self.get_playlist()
        pos = pl.find_by_path(track_path)
        if not pos:
            return
        del pl[pos[0]]
        await self._save(pl)

    async def clear(self):
        await self._save(Playlist([]))

    async def _save(self, pl: Playlist):
        _m3u_parser.dump(self.get_path(), pl)

    def get_path(self):
        return self.PATH_BASE / f"{self._broadcast.day}-{self._broadcast.num}"
