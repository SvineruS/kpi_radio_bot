"""Для корректной работы у плеера должен быть включен режим consume"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from pathlib import Path
from typing import List, Optional, Iterable

from mopidy import models
from mopidy_async_client import MopidyClient  # годная либа годный автор всем советую

from main import events
from utils import DateTime
from .playlist import PlaylistItem, Playlist


class PlayerMopidy:
    def __init__(self, **kwargs):
        self._CLIENT = MopidyClient(parse_results=True, **kwargs)

    async def connect(self):
        for _ in range(10):
            try:
                await self._CLIENT.connect()
                break
            except:
                logging.exception("Failed connect to mopidy")
                await asyncio.sleep(2)
        else:
            logging.exception("Failed connect to mopidy")
            exit(228)

        await self._CLIENT.tracklist.set_consume(True)

        self.bind_event("playback_state_changed", playback_state_changed)
        self.bind_event("track_playback_started", track_playback_started)

    async def set_volume(self, volume: int):
        return await self._CLIENT.mixer.set_volume(volume)

    async def next_track(self):
        await self._CLIENT.playback.next()

    async def set_next_track(self, pos: int):
        new_pos = await self._CLIENT.tracklist.index()
        return await self._CLIENT.tracklist.move(pos, pos, new_pos)

    async def get_playback(self) -> List[Optional[PlaylistItem]]:
        async def _get_prev():
            if not (history := await self._CLIENT.history.get_history()) or len(history) < 2:
                return None
            prev = await self._CLIENT.library.lookup(uris=[history[1][1].uri])
            return list(prev.values())[0][0]

        async def _get_next():
            if not (tlid := await self._CLIENT.tracklist.get_next_tlid()):
                return None
            next_ = await self._CLIENT.tracklist.filter({'tlid': [tlid]})
            return next_[0].track

        current = await self._CLIENT.playback.get_current_tl_track()
        current = getattr(current, 'track', None)

        res = [
            await _get_prev(),
            current,
            await _get_next()
        ]

        return [self.internal_to_playlist_item(i) if i else None for i in res]

    async def play_playlist(self, playlist: Playlist):
        uris = [_path_to_uri(track.path) for track in playlist]
        return await self._CLIENT.tracklist.add(uris=uris)

    async def play(self):
        return await self._CLIENT.playback.play()

    #

    async def get_playlist(self) -> Playlist:
        pl: List[PlaylistItem] = []
        for track in await self._CLIENT.tracklist.get_tracks():
            pl.append(self.internal_to_playlist_item(
                track,
                start_time=await self._get_start_time(pl[-1] if pl else None)
            ))
        return Playlist(pl)

    async def get_history(self) -> Iterable[PlaylistItem]:
        # todo
        pass

    async def add_track(self, track: PlaylistItem, position: Optional[int]) -> PlaylistItem:
        if position == -2:  # после текущего
            position = (await self._CLIENT.tracklist.index() or 0) + 1
        if position == -1:  # в конец
            position = None
        await self._CLIENT.tracklist.add(uris=[_path_to_uri(track.path)], at_position=position)
        pl = await self.get_playlist()
        return pl.find_by_path(track.path)[0]

    async def remove_track(self, track_path: Path) -> Optional[PlaylistItem]:
        tr = await self._CLIENT.tracklist.remove({'uri': [_path_to_uri(track_path)]})
        if tr:
            return self.internal_to_playlist_item(tr)

    async def clear(self):
        await self._CLIENT.tracklist.clear()

    #

    async def get_state(self):
        return await self._CLIENT.playback.get_state()

    def get_client(self):
        return self._CLIENT

    def bind_event(self, event, callback):
        return self._CLIENT.listener.bind(event, callback)

    async def _get_start_time(self, prev_item: PlaylistItem = None):
        if prev_item:
            return prev_item.stop_time
        return DateTime.now() - timedelta(milliseconds=await self._CLIENT.playback.get_time_position())

    @staticmethod
    def internal_to_playlist_item(track: models.Track, start_time=None) -> PlaylistItem:
        artist = list(track.artists)[0].name if track.artists else ""
        return PlaylistItem(
            performer=artist,
            title=track.name,
            path=Path(track.uri[7:]),  # remove 'file://' prefix
            duration=(track.length or 3*60*1000) // 1000,
            start_time=start_time
        )


# events

async def playback_state_changed(data):
    # state = stopped => плейлист пустой
    if data == {'old_state': 'playing', 'new_state': 'stopped'}:
        await events.ORDERS_QUEUE_EMPTY_EVENT.notify()


async def track_playback_started(data):
    track = PlayerMopidy.internal_to_playlist_item(data['tl_track'].track)
    await events.TRACK_BEGIN_EVENT.notify(track)


def _path_to_uri(path: Path):
    return "file://" + str(path.absolute())
