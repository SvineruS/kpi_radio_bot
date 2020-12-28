from __future__ import annotations

from datetime import datetime
from pathlib import Path

from utils.get_by import time_to_datetime
from ._base import PlaylistBase, PlaylistItem
from ..player import PlayerRadioboss


class PlaylistRadioboss(PlaylistBase):
    async def load(self) -> PlaylistRadioboss:
        self[:] = [
            PlaylistItem(
               title=track['@CASTTITLE'],
               time_start=time_to_datetime(datetime.strptime(track['@STARTTIME'], '%H:%M:%S').time()),  # set today
               path=track['@FILENAME'],
               duration=int((datetime.strptime(track['@STARTTIME'], '%H:%M:%S') - datetime(1900, 1, 1)).total_seconds())
            )
            for track in await PlayerRadioboss.get_playlist()
            if track['@STARTTIME']  # если STARTTIME == "" - это не песня (либо она стартанет через >=сутки)
        ]
        return self

    @staticmethod
    async def get_prev_now_next():
        pl = await PlayerRadioboss.get_prev_now_next()
        return [i["@CASTTITLE"] if i else None for i in pl]

    async def add_track(self, track: PlaylistItem, position: int = -1) -> PlaylistItem:
        track = await super().add_track(track, position)
        await PlayerRadioboss.add_track(track.path, position)
        return track

    async def remove_track(self, file_path: Path):
        pos, _ = await super().remove_track(file_path)
        await PlayerRadioboss.remove_track(pos)
