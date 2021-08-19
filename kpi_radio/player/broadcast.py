from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, List

from consts import others, config
from .backends import Playlist, PlaylistItem, DBPlaylistProvider, PlayerMopidy
from .player_utils import Exceptions, BroadcastGetters, get_random_from_archive


class Broadcast(BroadcastGetters):
    ALL: List[Broadcast] = []
    _local_playlist = DBPlaylistProvider
    player = PlayerMopidy(url=config.MOPIDY_URL)

    @property
    def playlist(self) -> DBPlaylistProvider:
        return self._local_playlist(self)

    async def get_playlist_next(self) -> Playlist:
        pl = await self.playlist.get_playlist()
        if self.is_now():
            return pl.trim(time_max=self.stop_time)
        return pl

    async def get_playback(self) -> Optional[List[PlaylistItem]]:
        return [
            await self.player.get_prev_track(),
            await self.player.get_current_track(),
            await self.playlist.get_next_track(),
        ] if self.is_now() else None

    async def get_free_time(self) -> int:  # seconds
        pl = (await self.playlist.get_playlist()).trim(time_max=self.stop_time)
        return max(0, self.duration(from_now=True) - pl.duration())

    async def add_track(self, track: PlaylistItem, position, audio) -> PlaylistItem:
        pl = await self.playlist.get_playlist()
        if pl.find_by_path(track.path):
            raise Exceptions.DuplicateException()
        if await self.get_free_time() < track.duration:
            raise Exceptions.NotEnoughSpaceException()

        if not track.path.exists():
            await audio.download(track.path)

        return await self.playlist.add_track(track, position)

    async def remove_track(self, track: PlaylistItem, remove_file=True):
        if remove_file:
            track.path.unlink(missing_ok=True)
        await self.playlist.remove_track(track.path)

    async def mark_played(self, path: Path) -> Optional[PlaylistItem]:
        return await self.playlist.remove_track(path)

    @classmethod
    async def play(cls, broadcast=None):
        track = (await broadcast.playlist.get_next_track() if broadcast else None) or get_random_from_archive()
        if not track:
            return logging.warning('No tracks to play')

        await cls.player.add_track(track)
        if await cls.player.play():
            return logging.info("Play " + str(track.path))

        logging.error("Failed to play " + str(track.path))
        if broadcast:
            await broadcast.remove_track(track, remove_file=False)
        await cls.play()


Broadcast.ALL = [Broadcast(day, num) for day, _num in others.BROADCAST_TIMES.items() for num in _num]
