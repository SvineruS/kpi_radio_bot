from pathlib import Path
from typing import Dict, List, Optional

from utils import DateTime
from . import _radioboss_api
from .._base import PlayerBase, PlaylistItem, Playlist


class PlayerRadioboss(PlayerBase):

    async def set_volume(self, volume: int):
        return await _radioboss_api.setvol(volume, 500)

    async def next_track(self):
        return await _radioboss_api.cmd_next()

    async def set_next_track(self, pos: int):
        return await _radioboss_api.setnexttrack(pos)

    async def get_playback(self) -> List[Optional[PlaylistItem]]:
        result: List[Optional[PlaylistItem]] = [None] * 3
        playback = await _radioboss_api.playbackinfo()
        if not playback or playback['Playback']['@state'] == 'stop':
            return result

        for i, k in enumerate(('PrevTrack', 'CurrentTrack', 'NextTrack')):
            if "setvol" not in playback[k]['TRACK']['@CASTTITLE']:
                result[i] = self.internal_to_playlist_item(playback[k]['TRACK'])
        return result

    async def play_playlist(self, path: Path):
        # радиобосс сейчас сам все делает
        pass

    async def play(self):
        # он и так никогда не останавливается, лень имплементировать
        pass

    #

    async def get_playlist(self) -> Playlist:
        pl = (await _radioboss_api.getplaylist2())['TRACK']
        for track in pl:
            cast_title = track['@CASTTITLE'].split(' - ')
            track['@ARTIST'] = cast_title[0] if len(cast_title) > 1 else ""
            track['@TITLE'] = cast_title[-1]

        return Playlist([
            self.internal_to_playlist_item(track)
            for track in pl
            if track['@STARTTIME']  # если STARTTIME == "" - это не песня (либо она стартанет через >=сутки)
        ])

    async def add_track(self, track: PlaylistItem, position: int) -> PlaylistItem:
        if position == -1:  # в очередь
            position = self._get_position_after_order()
        await _radioboss_api.inserttrack(track.path, position)
        pl = await self.get_playlist()
        return pl[pl.find_by_path(track.path)[0]]

    async def remove_track(self, track_path: Path):
        pl = await self.get_playlist()
        pos = pl.find_by_path(track_path)
        if not pos:
            return
        await _radioboss_api.delete(pos[0])

    async def clear(self):
        # ненадо
        pass

    #

    async def _get_position_after_order(self):
        pl = await self.get_playlist()
        for i, track in enumerate(pl):
            if not track.is_order:
                return i
        return -1  # все в плейлисте заказы -> будет последним

    @staticmethod
    def internal_to_playlist_item(track: Dict) -> PlaylistItem:
        return PlaylistItem(
            performer=track['@ARTIST'],
            title=track['@TITLE'],
            path=track['@FILENAME'],
            duration=DateTime.strpduration(track['@STARTTIME'], '%H:%M:%S'),
            start_time=DateTime.strptoday(track['@STARTTIME'], '%H:%M:%S')  # set today
        )
