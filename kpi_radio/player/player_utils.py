import logging
from random import choice
from typing import Optional

from consts import others
from .backends.playlist import PlaylistItem


def get_random_from_archive() -> Optional[PlaylistItem]:
    tracks = [p for p in others.PATH_MUSIC.iterdir()]
    if tracks:
        return PlaylistItem.from_path(choice(tracks))
    else:
        logging.warning("ARCHIVE is empty")
        return None
