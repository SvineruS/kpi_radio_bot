from consts import config
from .playlist import Playlist, PlaylistItem


class Backend:
    from .player_mopidy import PlayerMopidy
    from .playlist_db import DBPlaylistProvider

    _local_playlist = DBPlaylistProvider
    _player = PlayerMopidy(url=config.MOPIDY_URL)

    @classmethod
    def get_player(cls):
        return cls._player

    @classmethod
    def _get_local_playlist_provider(cls):
        return cls._local_playlist


__all__ = [
    'Playlist', 'PlaylistItem', 'Backend'
]
