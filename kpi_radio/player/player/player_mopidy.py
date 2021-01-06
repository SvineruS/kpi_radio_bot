from __future__ import annotations

from pathlib import Path
from typing import Dict, Union, List, Optional

from mopidy import models
from mopidy_async_client import MopidyClient  # годная либа годный автор всем советую

from ._base import PlayerBase


class PlayerMopidy(PlayerBase):
    _CLIENT = MopidyClient(parse_results=True)

    @classmethod
    async def set_volume(cls, volume):
        return await cls._CLIENT.mixer.set_volume(volume)

    @classmethod
    async def next_track(cls):
        return await cls._CLIENT.playback.next()

    @classmethod
    async def play(cls, tlid=None):
        return await cls._CLIENT.playback.play(tlid=tlid)

    @classmethod
    async def set_next_track(cls, pos):
        new_pos = await cls._CLIENT.tracklist.get_next_tlid()
        return await cls._CLIENT.tracklist.move(pos, pos, new_pos)

    @classmethod
    async def add_track(cls, path, position=0):
        position = None if position == -1 else position
        uri = cls._path_to_uri(path)
        r = await cls._CLIENT.tracklist.add(uris=[uri], at_position=position)
        await cls.play()
        return r

    @classmethod
    async def remove_track(cls, position_or_path: Union[Path, int]):
        if isinstance(position_or_path, Path):
            return await cls.remove_track_by_path(position_or_path)
        if isinstance(position_or_path, int):
            return await cls.remove_track_by_position(position_or_path)
        raise TypeError()

    @classmethod
    async def remove_track_by_path(cls, path: Path):
        uri = cls._path_to_uri(path)
        return await cls._CLIENT.tracklist.remove({'uri': [uri]})

    @classmethod
    async def remove_track_by_position(cls, position: int):
        return await cls._CLIENT.tracklist.remove({'tlid': [position]})

    @classmethod
    async def get_playlist(cls) -> Dict[int, models.Track]:
        return {
            i.tlid: i.track
            for i in await cls._CLIENT.tracklist.get_tl_tracks()
        }

    @classmethod
    async def get_next_tlid(cls):
        return await cls._CLIENT.tracklist.get_next_tlid()

    @classmethod
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
    async def get_state(cls):
        return await cls._CLIENT.playback.get_state()

    @classmethod
    def get_client(cls):
        return cls._CLIENT

    @classmethod
    def bind_event(cls, event, callback):
        return cls._CLIENT.listener.bind(event, callback)

    @classmethod
    def _path_to_uri(cls, path: Path):
        return "file://" + str(path.absolute())

    @classmethod
    async def play_playlist(cls, path: Path):
        uri = "m3u://" + str(path.absolute())
        await cls._CLIENT.tracklist.clear()
        await cls._CLIENT.tracklist.add(uris=[uri])
        await cls.play()
