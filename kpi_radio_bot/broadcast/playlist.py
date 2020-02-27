from datetime import datetime
from pathlib import Path

import consts
from broadcast.broadcast import get_broadcast_num, is_this_broadcast_now, get_broadcast_path
from broadcast.radioboss import radioboss_api


async def get_now():
    playback = await radioboss_api(action='playbackinfo')
    result = [r'¯\_(ツ)_/¯'] * 3
    if not playback or playback[3].attrib['state'] == 'stop':
        return None
    for i in range(3):
        title = playback[i][0].attrib['CASTTITLE']
        if "setvol" in title:
            continue

        result[i] = title
    return result


async def get_next():
    playlist = await get_playlist()
    b_n = get_broadcast_num()
    if not playlist or b_n is False:
        return []

    result = []

    dt_now = datetime.now()
    time_min = dt_now.time()
    time_max = consts.BROADCAST_TIMES[dt_now.weekday()][b_n][1]
    time_max = datetime.strptime(time_max, '%H:%M').time()

    for track in playlist:
        time_start = track["time_start"].time()
        if time_start < time_min:
            continue
        if time_start > time_max:
            break
        result.append(track)

    return result


async def get_playlist():
    result = []
    playlist = await radioboss_api(action='getplaylist2')
    if not playlist:
        return []

    for track in playlist:
        track = track.attrib
        if not track['STARTTIME']:  # если STARTTIME == "" скорее всего это не песня (либо она стартанет через >=сутки)
            continue

        result.append({
            'title': track['CASTTITLE'],
            'time_start': datetime.strptime(track['STARTTIME'], '%H:%M:%S'),
            'filename': track['FILENAME'],
            'index': int(track['INDEX']),
            'is_order': str(consts.PATHS['orders']) in track["FILENAME"]
        })

    return result


async def get_new_order_pos():
    playlist = await get_next()
    if not playlist:
        return False
    for i in range(len(playlist) - 1, -1, -1):
        track = playlist[i]
        if track["is_order"]:
            if i == len(playlist) - 1:  # если последний трек что успеет проиграть это заказ то пизда, вернем False
                return False
            return playlist[i + 1]  # иначе вернем трек которй будет играть после заказа
    return playlist[0]  # если нету заказов - вернуть самый первый трек в очереди


async def find_in_playlist_by_path(path):
    return [i for i in await get_playlist() if i['filename'] == path]


async def get_broadcast_freetime(day: int, time: int) -> int:
    broadcast_start, broadcast_finish = consts.BROADCAST_TIMES_[day][time]
    if is_this_broadcast_now(day, time):
        last_order = await get_new_order_pos()
        if not last_order:
            return 0
        last_order_start = last_order['time_start'].hour * 60 + last_order['time_start'].minute
    else:
        tracks_duration = await _calculate_tracks_duration(get_broadcast_path(day, time))
        last_order_start = broadcast_start + tracks_duration

    return max(0, broadcast_finish - last_order_start)


#


async def _calculate_tracks_duration(path: Path) -> float:
    duration = 0
    try:
        files = path.iterdir()
        for file in files:
            tags = await radioboss_api(action='readtag', fn=file)
            if tags:
                duration += int(tags[0].attrib['Duration'])
    except FileNotFoundError:
        return 0
    return duration / 1000 / 60  # minutes
