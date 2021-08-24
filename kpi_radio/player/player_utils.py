import logging
from random import choice
from typing import Optional

from consts import others
from .backends.playlist import PlaylistItem


class Exceptions:
    class RadioExceptions(Exception):
        pass

    class NotEnoughSpaceException(RadioExceptions):
        pass

    class DuplicateException(RadioExceptions):
        pass


def get_random_from_archive() -> Optional[PlaylistItem]:
    tracks = [p for p in others.PATH_MUSIC.iterdir()]
    if tracks:
        return PlaylistItem.from_path(choice(tracks))
    else:
        logging.warning("ARCHIVE is empty")
        return None
