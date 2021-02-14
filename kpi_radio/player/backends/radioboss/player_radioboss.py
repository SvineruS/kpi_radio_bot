from pathlib import Path
from typing import Dict, List, Optional, Iterable

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

    async def get_history(self) -> Iterable[PlaylistItem]:
        lastplayed = await _radioboss_api.getlastplayed()
        return map(self.internal_to_playlist_item, lastplayed['TRACK'])

    async def play_playlist(self, playlist: Playlist):
        # радиобосс сейчас сам все делает
        pass

    async def play(self):
        # он и так никогда не останавливается, лень имплементировать
        pass

    #

    async def get_playlist(self) -> Playlist:
        pl = (await _radioboss_api.getplaylist2())['TRACK']
        return Playlist([
            self.internal_to_playlist_item(track)
            for track in pl
            if track['@STARTTIME']  # если STARTTIME == "" - это не песня (либо она стартанет через >=сутки)
        ])

    async def add_track(self, track: PlaylistItem, position: int) -> PlaylistItem:
        if position == -1:  # в очередь
            position = await self._get_position_after_order()
        await _radioboss_api.inserttrack(track.path, position)
        pl = await self.get_playlist()
        return pl.find_by_path(track.path)[0]

    async def remove_track(self, track_path: Path) -> Optional[PlaylistItem]:
        pl = await self.get_playlist()
        tracks = pl.find_by_path(track_path)
        for track in tracks:
            await _radioboss_api.delete(track._index)
            return track
        return None

    async def clear(self):
        # ненадо
        pass

    #

    async def _get_position_after_order(self) -> int:
        pl = await self.get_playlist()
        for track in pl[1:]:
            if not track.is_order:
                return track._index
        return -1  # все в плейлисте заказы -> будет последним

    @staticmethod
    def internal_to_playlist_item(track: Dict) -> PlaylistItem:
        if not track.get('@ARTIST', None) or not track.get('@TITLE', None):
            cast_title = track['@CASTTITLE'].split(' - ')
            track['@ARTIST'] = cast_title[0] if len(cast_title) > 1 else ""
            track['@TITLE'] = cast_title[-1]

        start_time = None
        if '@STARTTIME' in track:
            if len(track['@STARTTIME']) > 10:
                start_time = DateTime.strptime(track['@STARTTIME'], '%Y-%m-%d %H:%M:%S')
            else:
                start_time = DateTime.strptoday(track['@STARTTIME'], '%H:%M:%S')  # set today

        item = PlaylistItem(
            performer=track['@ARTIST'],
            title=track['@TITLE'],
            path=Path(track['@FILENAME']),
            duration=DateTime.strpduration(track['@DURATION'], '%M:%S') if '––:––' not in track['@DURATION'] else 0,
            start_time=start_time
        )
        item._index = int(track.get('@INDEX', -1))
        return item
