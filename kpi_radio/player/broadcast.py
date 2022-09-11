from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, List

from consts import config
from .backends import Playlist, PlaylistItem, DBPlaylistProvider, PlayerMopidy
from .ether import Ether
from .player_utils import get_random_from_archive


class Broadcast:
    player = PlayerMopidy(url=config.MOPIDY_URL)

    def __init__(self, ether: Optional[Ether]):
        self.ether: Optional[Ether] = ether

    def is_ether_now(self):
        return self.ether and self.ether.now()

    @property
    def playlist(self) -> DBPlaylistProvider:
        return DBPlaylistProvider(self.ether)

    async def get_next_track(self) -> Optional[PlaylistItem]:
        if r := await DBPlaylistProvider(Ether.OUT_OF_QUEUE).get_next_track():
            return r
        elif self.ether:
            return await DBPlaylistProvider(self.ether).get_next_track()

    async def get_next_tracklist(self) -> Playlist:
        pl_out_of_queue = await DBPlaylistProvider(Ether.OUT_OF_QUEUE).get_playlist()
        if not self.ether:
            return pl_out_of_queue

        pl_ether = await self.playlist.get_playlist()
        pl = Playlist(
            pl_out_of_queue.trim_by(self.ether) + pl_ether,
            time_start=pl_ether.time_start
        )
        return pl.trim_by(self.ether)

    async def get_playback(self) -> List[Optional[PlaylistItem]]:
        return [
            await self.player.get_prev_track(),
            await self.player.get_current_track(),
            await self.get_next_track(),
        ] if self.is_ether_now() else [None] * 3

    async def get_free_time(self, pl=None) -> int:  # seconds
        pl = pl or await self.get_next_tracklist()
        return max(0, self.ether.duration(from_now=True) - pl.duration())

    async def add_track(self, track: PlaylistItem, audio) -> Optional[PlaylistItem]:
        if not track.path.exists():
            await audio.download(track.path)
        await self.playlist.add_track(track)
        if not self.is_ether_now():
            return track
        return (await self.get_next_tracklist()).find_by_path(track.path)[0]

    async def remove_track(self, track: PlaylistItem, remove_file=False):
        if remove_file:
            track.path.unlink(missing_ok=True)
        await self.playlist.remove_track(track.path)

    async def mark_played(self, path: Path) -> Optional[PlaylistItem]:
        return await DBPlaylistProvider(Ether.OUT_OF_QUEUE).remove_track(path) or \
               await self.playlist.remove_track(path)

    async def play(self):
        track = await self.get_next_track() or get_random_from_archive()
        if not track:
            return logging.warning('No tracks to play')

        await self.player.add_track(track)
        if await self.player.play():
            return logging.info("Play " + str(track.path))

        logging.error("Failed to play " + str(track.path))
        await Broadcast(track.ether).remove_track(track)
        await self.play()
