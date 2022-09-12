from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from consts import config, others
from player.ether import Ether
from utils import db, DateTime
from .playlist import Playlist, PlaylistItem


class DBPlaylistProvider:
    PATH_BASE = config.PATH_STUFF / 'playlists'

    def __init__(self, ether):
        self.ether: Ether = ether

    async def get_next_track(self) -> Optional[PlaylistItem]:
        if track := db.Tracklist.get_by_ether(self.ether).first():
            return self.internal_to_playlist_item(track, start_time=await self._get_start_time())

    async def get_playlist(self) -> Playlist:
        pl = db.Tracklist.get_by_ether(self.ether)
        return Playlist(
            map(self.internal_to_playlist_item, pl),
            time_start=await self._get_start_time()
        )

    async def add_track(self, track: PlaylistItem):
        db.Tracklist.add(track, self.ether)

    async def remove_track(self, track_path: Path) -> Optional[PlaylistItem]:
        if track := db.Tracklist.remove_track(self.ether, track_path):
            return self.internal_to_playlist_item(track)

    async def clear(self):
        db.Tracklist.clear_ether(self.ether)

    async def _get_start_time(self):
        if self.ether == Ether.OUT_OF_QUEUE:
            return DateTime.now()

        if self.ether.is_now():
            from player import Broadcast
            return await Broadcast.player.current_track_stop_time()

        return self.ether.start_time

    def internal_to_playlist_item(self, track: db.Tracklist, start_time=None) -> PlaylistItem:
        return PlaylistItem(
            performer=track.track_performer,
            title=track.track_title,
            path=others.PATH_MUSIC / track.track_path,
            duration=track.track_duration,
            start_time=start_time,
            ether=self.ether
        ).add_track_info(
            user_id=track.info_user_id,
            user_name=track.info_user_name,
            moderation_msg_id=track.info_message_id
        )
