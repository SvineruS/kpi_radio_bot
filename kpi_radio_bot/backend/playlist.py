from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import List, Union

from backend import radioboss
from consts import others
from utils.get_by import time_to_datetime

PlaylistItem = namedtuple("namedtuple", ('title', 'time_start', 'filename', 'index_', 'is_order'))
PlayList = List[PlaylistItem]


async def get_now():
    playback = await radioboss.playbackinfo()
    if not playback or playback['Playback']['@state'] == 'stop':
        return None

    result = [''] * 3
    for i, k in enumerate(('PrevTrack', 'CurrentTrack', 'NextTrack')):
        title = playback[k]['TRACK']['@CASTTITLE']
        if "setvol" not in title:
            result[i] = title
    return result


async def get_playlist() -> PlayList:
    if not (playlist := await radioboss.getplaylist2()):
        return []

    result = []
    for track in playlist['TRACK']:
        if not track['@STARTTIME']:  # если STARTTIME == "" - это не песня (либо она стартанет через >=сутки)
            continue

        track = PlaylistItem(
            title=track['@CASTTITLE'],
            time_start=time_to_datetime(datetime.strptime(track['@STARTTIME'], '%H:%M:%S').time()),  # set today
            filename=track['@FILENAME'],
            index_=int(track['@INDEX']),
            is_order=str(others.PATHS['orders']) in track['@FILENAME']
        )
        result.append(track)

    return result


async def get_bounded_playlist(time_min: datetime = None, time_max: datetime = None) -> PlayList:
    if not (playlist := await get_playlist()):
        return []

    result = []
    for track in playlist:
        time_start = track.time_start
        if time_min and time_start < time_min:
            continue
        if time_max and time_start > time_max:
            break
        result.append(track)

    return result


async def get_playlist_next() -> PlayList:
    return await get_bounded_playlist(datetime.now())


async def find_in_playlist_by_path(path: Union[str, Path]) -> PlayList:
    path = str(path)
    return [track for track in await get_playlist() if track.filename == path]
