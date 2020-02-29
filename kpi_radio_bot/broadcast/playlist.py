from collections import namedtuple
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Union

import consts
from broadcast.broadcast import get_broadcast_num, is_this_broadcast_now
from broadcast.radioboss import radioboss_api
from utils.get_by import time_to_datetime
from utils.files import get_downloaded_tracks

PlaylistItem = namedtuple("namedtuple", ('title', 'time_start', 'filename', 'index', 'is_order'))


async def get_now():
    playback = await radioboss_api(action='playbackinfo')
    if not playback or playback[3].attrib['state'] == 'stop':
        return False

    result = [''] * 3
    for i, track in enumerate(playback[0:2]):
        title = track[0].attrib['CASTTITLE']
        if "setvol" not in title:
            result[i] = title

    return result


async def get_next() -> List[PlaylistItem]:
    playlist = await _get_playlist()
    b_n = get_broadcast_num()
    if not playlist or b_n is False:
        return []

    dt_now = datetime.now()
    time_min = dt_now.time()
    time_max = consts.BROADCAST_TIMES_[dt_now.weekday()][b_n][1]

    result = []
    for track in playlist:
        time_start = track.time_start.time()
        if time_start < time_min:
            continue
        if time_start > time_max:
            break
        result.append(track)

    return result


async def get_new_order_pos() -> Union[None, PlaylistItem]:
    playlist = await get_next()
    if not playlist or playlist[-1].is_order:  # если последний трек, что успеет проиграть, это заказ - вернем None
        return None

    for i, track in reversed(list(enumerate(playlist[:-1]))):
        if track.is_order:  # т.к. заказы всегда в начале плейлиста, то нужен трек, следующий после последнего заказа
            return playlist[i + 1]
    return playlist[0]  # если нету заказов - вернуть самый первый трек в очереди


async def find_in_playlist_by_path(path: Union[str, Path]) -> List[PlaylistItem]:
    path = str(path)
    return [track for track in await _get_playlist() if track.filename == path]


async def get_broadcast_freetime(day: int, time: int) -> int:
    broadcast_start, broadcast_finish = map(time_to_datetime, consts.BROADCAST_TIMES_[day][time])

    if is_this_broadcast_now(day, time):
        last_order = await get_new_order_pos()
        if not last_order:
            return 0
        last_order_start = last_order.time_start
    else:
        tracks_duration = await _calculate_tracks_duration(day, time)
        last_order_start = broadcast_start + timedelta(minutes=tracks_duration)

    t_d = broadcast_finish - last_order_start
    t_d = int(t_d.total_seconds() // 60)
    return max(0, t_d)


#

async def _get_playlist() -> List[PlaylistItem]:
    playlist = await radioboss_api(action='getplaylist2')
    if not playlist:
        return []

    result = []
    for track in playlist:
        track = track.attrib
        if not track['STARTTIME']:  # если STARTTIME == "" скорее всего это не песня (либо она стартанет через >=сутки)
            continue

        track = PlaylistItem(
            title=track['CASTTITLE'],
            time_start=time_to_datetime(datetime.strptime(track['STARTTIME'], '%H:%M:%S').time()),  # set today date
            filename=track['FILENAME'],
            index=int(track['INDEX']),
            is_order=str(consts.PATHS['orders']) in track["FILENAME"]
        )
        result.append(track)

    return result


async def _calculate_tracks_duration(day: int, time: int) -> float:
    duration = 0
    try:
        for file in get_downloaded_tracks(day, time):
            tags = await radioboss_api(action='readtag', fn=file)
            if tags:
                duration += int(tags[0].attrib['Duration'])
    except FileNotFoundError:  # это бблядь как
        return 0
    return duration / 1000 / 60  # minutes
