"""Для корректной работы у плеера должен быть включен режим consume"""

from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
from typing import Optional, Iterable

from mopidy import models
from mopidy_async_client import MopidyClient  # годная либа годный автор всем советую

from main import events
from utils import DateTime
from .playlist import PlaylistItem


class PlayerMopidy:
    def __init__(self, **kwargs):
        self._CLIENT = MopidyClient(parse_results=True, **kwargs)

        self._CLIENT.listener.bind("track_playback_ended", lambda _: events.ORDERS_QUEUE_EMPTY_EVENT.notify())
        self._CLIENT.listener.bind("track_playback_started", lambda data:
                                   events.TRACK_BEGIN_EVENT.notify(_internal_to_playlist_item(data['tl_track'].track)))

    async def connect(self):
        await self._CLIENT.connect()
        await self._CLIENT.tracklist.set_consume(True)  # треки убираются из треклиста когда играют

    #

    async def play(self) -> bool:
        if self._CLIENT.playback.get_state() != 'playing':
            await self._CLIENT.playback.play()
            await asyncio.sleep(0.2)
        return await self._CLIENT.playback.get_current_track() is not None

    async def set_volume(self, volume: int):
        return await self._CLIENT.mixer.set_volume(volume)

    async def next_track(self):
        await self._CLIENT.playback.next()

    # tracks

    async def get_prev_track(self):
        if not (history := await self._CLIENT.history.get_history()) or len(history) < 2:
            return None
        prev = await self._CLIENT.library.lookup(uris=[history[1][1].uri])
        prev = list(prev.values())[0][0]
        return _internal_to_playlist_item(prev)

    async def get_current_track(self):
        if not (current := await self._CLIENT.playback.get_current_track()):
            return None
        return _internal_to_playlist_item(current)

    async def get_next_track(self):  # not used
        if not (tlid := await self._CLIENT.tracklist.get_next_tlid()):
            return None
        next_ = await self._CLIENT.tracklist.filter({'tlid': [tlid]})
        return _internal_to_playlist_item(next_[0].track)

    #

    async def add_track(self, track: PlaylistItem):
        await self._CLIENT.tracklist.add(uris=[_path_to_uri(track.path)])

    async def remove_track(self, track_path: Path) -> Optional[PlaylistItem]:
        if tr := await self._CLIENT.tracklist.remove({'uri': [_path_to_uri(track_path)]}):
            return _internal_to_playlist_item(tr)

    async def set_next_track(self, pos: int):
        new_pos = await self._CLIENT.tracklist.index()
        return await self._CLIENT.tracklist.move(pos, pos, new_pos)

    #

    async def current_track_stop_time(self) -> DateTime:
        if track := await self.get_current_track():
            return DateTime.now() + timedelta(seconds=track.duration) - \
                   timedelta(milliseconds=await self._CLIENT.playback.get_time_position())

    async def get_history(self) -> Iterable[PlaylistItem]:
        # todo
        pass

    def get_client(self):
        return self._CLIENT


# utils

def _internal_to_playlist_item(track: models.Track) -> PlaylistItem:
    artist = list(track.artists)[0].name if track.artists else ""
    return PlaylistItem(
        performer=artist,
        title=track.name,
        path=Path(track.uri[7:]),  # remove 'file://' prefix
        duration=(track.length or 3*60*1000) // 1000,  # default 3 min
    )


def _path_to_uri(path: Path):
    return "file://" + str(path.absolute())

