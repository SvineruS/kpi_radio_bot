import abc
from pathlib import Path
from typing import List, Optional, Iterable

from .playlist import PlaylistItem, Playlist


class IPlaylistProvider(abc.ABC):
    async def get_playlist(self) -> Playlist:
        raise NotImplementedError

    async def add_track(self, track: PlaylistItem, position: int) -> PlaylistItem:
        raise NotImplementedError

    async def remove_track(self, track_path: Path) -> Optional[PlaylistItem]:
        raise NotImplementedError

    async def clear(self):
        raise NotImplementedError


class PlayerBase(IPlaylistProvider, abc.ABC):
    async def set_volume(self, volume: int):
        raise NotImplementedError

    async def next_track(self):
        raise NotImplementedError

    async def set_next_track(self, pos: int):
        raise NotImplementedError

    async def get_playback(self) -> List[Optional[PlaylistItem]]:
        raise NotImplementedError

    async def get_history(self) -> Iterable[PlaylistItem]:
        raise NotImplementedError

    async def play_playlist(self, playlist: Playlist):
        raise NotImplementedError

    async def play(self):
        raise NotImplementedError


class LocalPlaylistProviderBase(IPlaylistProvider, abc.ABC):
    def __init__(self, broadcast):
        self._broadcast = broadcast
