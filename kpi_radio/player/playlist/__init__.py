
from ._base import PlaylistBase, PlaylistItem
from .playlist_local import PlaylistM3U
from .playlist_mopidy import PlaylistMopidy
from .playlist_radioboss import PlaylistRadioboss

PlaylistNow = PlaylistMopidy


__all__ = [
    'PlaylistNow', 'PlaylistM3U',
    'PlaylistMopidy', 'PlaylistRadioboss',
    'PlaylistBase', 'PlaylistItem'
]
