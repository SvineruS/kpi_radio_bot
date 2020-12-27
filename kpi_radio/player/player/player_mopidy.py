from __future__ import annotations

import asyncio
import functools
from typing import Dict, Tuple

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
        pass

    @classmethod
    @connection
    async def add_track(cls, path, position):
        return await cls._CLIENT.tracklist.add()
        # todo

    @classmethod
    @connection
    async def remove_track(cls, position):
        return await cls._CLIENT.tracklist.remove()
            # todo

    @classmethod
    @connection
    async def get_playlist(cls) -> Dict[int, models.Track]:
        return {
            i.tlid: i.track
            for i in await cls._CLIENT.tracklist.get_tl_tracks()
        }

    @classmethod
    @connection
    async def get_prev_now_next(cls) -> Tuple[models.Track, models.Track, models.Track]:
        pl = await cls.get_playlist()
        cur = await cls._CLIENT.playback.get_current_tlid()
        return (
            pl.get(cur-1, None),
            pl.get(cur, None),
            pl.get(cur+1, None),
        )
