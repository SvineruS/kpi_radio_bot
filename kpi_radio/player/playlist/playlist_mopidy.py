from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from ._base import PlaylistBase, PlaylistItem
from ..player import PlayerMopidy


class PlaylistMopidy(PlaylistBase):
    async def load(self) -> PlaylistBase:
        self[:] = []
        duration_sum = timedelta()
        for index, track in (await PlayerMopidy.get_playlist()).items():
            self.append(PlaylistItem(
                title=track.name,
                path=Path(track.uri),
                duration=track.length,
                time_start=self.broadcast.start_time + duration_sum
            ))
            duration_sum += timedelta(seconds=track.length)
        return self

    @staticmethod
    async def get_prev_now_next():
        return await PlayerMopidy.get_prev_now_next()

    async def add_track(self, track, position=-1):
        await super().add_track(track, position)
        await PlayerMopidy.add_track(track.path, position)

    async def remove_track(self, file_path):
        pos = await super().remove_track(file_path)
        await PlayerMopidy.remove_track(pos)

