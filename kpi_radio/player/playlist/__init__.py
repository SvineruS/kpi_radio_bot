from typing import Union

from ._base import PlaylistBase, PlaylistItem
from .playlist_local import PlaylistM3U
from .playlist_radioboss import PlaylistRadioboss
from .playlist_mopidy import PlaylistMopidy


PlaylistNow = PlaylistMopidy


class Playlist(PlaylistM3U, PlaylistNow):
    def __new__(cls, broadcast, seq=()) -> Union[PlaylistM3U, PlaylistNow]:
        if broadcast.is_now():
            return PlaylistNow(broadcast, seq)
        else:
            return PlaylistM3U(broadcast, seq)


__all__ = [
    'Playlist', 'PlaylistNow', 'PlaylistM3U',
    'PlaylistMopidy', 'PlaylistRadioboss',
    'PlaylistBase', 'PlaylistItem'
]
