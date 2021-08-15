from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from consts import config, others
from utils import db, DateTime
from .playlist import Playlist, PlaylistItem


class DBPlaylistProvider:
    PATH_BASE = config.PATH_STUFF / 'playlists'

    def __init__(self, broadcast):
        self._broadcast = broadcast

    async def get_next_track(self) -> PlaylistItem:
        if track := db.Tracklist.get_by_broadcast(*self._broadcast).first():
            return internal_to_playlist_item(track, start_time=await self._get_start_time())

    async def get_playlist(self) -> Playlist:
        pl_ = db.Tracklist.get_by_broadcast(*self._broadcast)

        pl: List[PlaylistItem] = []
        for track in pl_:
            pl.append(internal_to_playlist_item(
                track,
                start_time=await self._get_start_time(pl[-1] if pl else None)
            ))
        return Playlist(pl)

    async def add_track(self, track: PlaylistItem, position: Optional[int]) -> PlaylistItem:
        if position == -2:  # после текущего
            position = 0
        if position == -1:  # в конец
            position = None
        db.Tracklist.add(position, track, self._broadcast)
        pl = await self.get_playlist()
        return pl.find_by_path(track.path)[0]  # проставляем start_time

    async def remove_track(self, track_path: Path) -> Optional[PlaylistItem]:
        track = db.Tracklist.remove_track(self._broadcast.day, self._broadcast.num, track_path)
        if not track:
            return None
        return internal_to_playlist_item(track)

    async def clear(self):
        db.Tracklist.remove_tracks(self._broadcast.day, self._broadcast.num)

    async def _get_start_time(self, prev_item: PlaylistItem = None):
        if prev_item:
            return prev_item.stop_time
        if self._broadcast.now():
            return await self._broadcast.player.current_track_stop_time()
        return DateTime.now()


def internal_to_playlist_item(track: db.Tracklist, start_time=None) -> PlaylistItem:
    return PlaylistItem(
        performer=track.track_performer,
        title=track.track_title,
        path=others.PATH_MUSIC / track.track_path,
        duration=track.track_duration,
        start_time=start_time
    ).add_track_info(
        user_id=track.info_user_id,
        user_name=track.info_user_name,
        moderation_msg_id=track.info_message_id
    )