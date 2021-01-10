from typing import Type

from ._base import PlayerBase, LocalPlaylistProviderBase, Playlist, PlaylistItem, IPlaylistProvider


class Descriptor:
    def __init__(self, f):
        self.f = f

    def __get__(self, instance=None, owner=None):
        return self.f()

    def __call__(self, *args, **kwargs):
        return self.f().__call__(*args, **kwargs)

    def __getattr__(self, item):
        return getattr(self.f(), item)


_player: PlayerBase
_local_playlist: Type[LocalPlaylistProviderBase]


# todo пиздец некрасиво
Player: PlayerBase = Descriptor(lambda: _player)
LocalPlaylist: Type[LocalPlaylistProviderBase] = Descriptor(lambda: _local_playlist)


def register_backends(player: PlayerBase, local_playlist: Type[LocalPlaylistProviderBase]):
    global _player, _local_playlist
    _player, _local_playlist = player, local_playlist


__all__ = [
    'Player', 'LocalPlaylist', 'IPlaylistProvider',
    'Playlist', 'PlaylistItem',
    'register_backends'
]



