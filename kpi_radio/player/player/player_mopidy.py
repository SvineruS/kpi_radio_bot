from __future__ import annotations

import functools
from pathlib import Path
from typing import Dict, Tuple, Union, List, Optional

from mopidy_async_client import MopidyClient  # годная либа годный автор всем советую
from mopidy import models

from ._base import PlayerBase


def connection(function):
    @functools.wraps(function)
    async def on_call(cls: PlayerMopidy, *args, **kwargs):
        if cls._CLIENT is None:
            cls._CLIENT = await MopidyClient(parse_results=True).connect()
        return await function(cls, *args, **kwargs)
    return on_call


class PlayerMopidy(PlayerBase):

    _CLIENT: MopidyClient = None

    @classmethod
    @connection
    async def set_volume(cls, volume):
        return await cls._CLIENT.mixer.set_volume(volume)

    @classmethod
    @connection
    async def next_track(cls):
        return await cls._CLIENT.playback.next()

    @classmethod
    @connection
    async def set_next_track(cls, pos):
        new_pos = await cls._CLIENT.tracklist.get_next_tlid()
        return await cls._CLIENT.tracklist.move(pos, pos, new_pos)

    @classmethod
    @connection
    async def add_track(cls, path, position):
        position = None if position == -1 else position
        uri = cls._path_to_uri(path)
        return await cls._CLIENT.tracklist.add(uris=[uri], at_position=position)

    @classmethod
    async def remove_track(cls, position_or_path: Union[Path, int]):
        if isinstance(position_or_path, Path):
            return await cls.remove_track_by_path(position_or_path)
        if isinstance(position_or_path, int):
            return await cls.remove_track_by_position(position_or_path)
        raise TypeError()

    @classmethod
    @connection
    async def remove_track_by_path(cls, path: Path):
        uri = cls._path_to_uri(path)
        return await cls._CLIENT.tracklist.remove({'uri': [uri]})

    @classmethod
    @connection
    async def remove_track_by_position(cls, position: int):
        return await cls._CLIENT.tracklist.remove({'tlid': [position]})

    @classmethod
    @connection
    async def get_playlist(cls) -> Dict[int, models.Track]:
        return {
            i.tlid: i.track
            for i in await cls._CLIENT.tracklist.get_tl_tracks()
        }

    @classmethod
    @connection
    async def get_prev_now_next(cls) -> List[Optional[models.Track]]:
        pl = await cls.get_playlist()
        cur = await cls._CLIENT.playback.get_current_tlid()
        if not cur:
            return [None] * 3
        return [
            pl.get(cur-1, None),
            pl.get(cur, None),
            pl.get(cur+1, None),
        ]

    @classmethod
    @connection
    async def get_client(cls):
        return cls._CLIENT

    @classmethod
    def _path_to_uri(cls, path: Path):
        return "file://" + str(path)
