from __future__ import annotations

from pathlib import Path

from ._base import PlaylistBase, PlaylistItem
from ..player import PlayerMopidy


class PlaylistMopidy(PlaylistBase):
    async def load(self) -> PlaylistBase:
        self[:] = []
        for track in (await PlayerMopidy.get_playlist()).values():
            self.append(self.tl_to_pl(track, start_time=self._get_start_time()))
        return self

    @staticmethod
    async def get_prev_now_next():
        pl = await PlayerMopidy.get_prev_now_next()
        return [i.name if i else None for i in pl]

    async def add_track(self, track: PlaylistItem, position: int = -1) -> PlaylistItem:
        track = await super().add_track(track, position)
        await PlayerMopidy.add_track(track.path, position)
        return track

    async def remove_track(self, file_path: Path):
        await super().remove_track(file_path)
        await PlayerMopidy.remove_track(file_path)

    @staticmethod
    def tl_to_pl(tl, start_time=None):
        return PlaylistItem(
            title=tl.name,
            path=Path(tl.uri),
            duration=tl.length,
            time_start=start_time
        )
