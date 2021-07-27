from typing import Type

from ._base import PlayerBase, LocalPlaylistProviderBase, Playlist, PlaylistItem


class Backend:
    _player: PlayerBase
    _local_playlist: Type[LocalPlaylistProviderBase]

    @classmethod
    def get_player(cls) -> PlayerBase:
        return cls._player

    @classmethod
    def _get_local_playlist_provider(cls) -> Type[LocalPlaylistProviderBase]:
        return cls._local_playlist

    @classmethod
    def register_backends(cls, player: PlayerBase, local_playlist: Type[LocalPlaylistProviderBase]):
        cls._player, cls._local_playlist = player, local_playlist


__all__ = [
    'Playlist', 'PlaylistItem', 'Backend'
]
