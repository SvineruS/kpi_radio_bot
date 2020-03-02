from collections import namedtuple
from typing import Optional, List, Union

from datetime import datetime, timedelta
from pathlib import Path

import files
import get_by
import other
from consts import others
from . import radioboss
from get_by import time_to_datetime
from other import my_lru


class Broadcast:
    @my_lru()
    def __new__(cls, day: int, num: int):
        return super().__new__(cls)

    def __init__(self, day: int, num: int):
        if day not in others.BROADCAST_TIMES_:
            raise Exception("wrong day")
        if num not in others.BROADCAST_TIMES_[day]:
            raise Exception("wrong num")

        self.day: int = day
        self.num: int = num

    def path(self) -> Path:
        path = others.PATHS['orders']
        path /= f"D0{self.day + 1}"
        path /= '{0} {1}'.format(self.num, others.TIMES[self.num])
        return path

    def name(self) -> str:
        return ', '.join((others.WEEK_DAYS[self.day], others.TIMES[self.num]))

    def start_time(self) -> datetime:
        return time_to_datetime(others.BROADCAST_TIMES_[self.day][self.num][0])

    def stop_time(self) -> datetime:
        return time_to_datetime(others.BROADCAST_TIMES_[self.day][self.num][1])

    def is_today(self) -> bool:
        return self.day == datetime.now().weekday()

    def is_now(self) -> bool:
        return self.start_time() < datetime.now() < self.stop_time()

    def is_will_be_play_today(self) -> bool:
        return self.is_today() and self.start_time() < datetime.now()

    def is_already_play_today(self) -> bool:
        return self.is_today() and self.stop_time() > datetime.now()

    async def get_free_time(self) -> float:
        return await get_free_time(self)

    @classmethod
    def now(cls):
        for day, _num in others.BROADCAST_TIMES_.items():
            for num in _num:
                if (broadcast := Broadcast(day, num)).is_now():
                    return broadcast

    def __iter__(self) -> int:
        yield self.day
        yield self.num

    @classmethod
    def is_broadcast_right_now(cls) -> bool:
        return cls.now() is not None


# playlist


PlaylistItem = namedtuple("namedtuple", ('title', 'time_start', 'filename', 'index', 'is_order'))


async def get_now() -> Optional[List[str]]:
    playback = await radioboss.playbackinfo()
    if not playback or playback['Playback']['@state'] == 'stop':
        return None

    result = [''] * 3
    for i, k in enumerate(('PrevTrack', 'CurrentTrack', 'NextTrack')):
        title = playback[k]['TRACK']['@CASTTITLE']
        if "setvol" not in title:
            result[i] = title

    return result


async def get_next() -> List[PlaylistItem]:
    if not (playlist := await _get_playlist()):
        return []

    broadcast = Broadcast.now()
    time_min = datetime.now()
    time_max = broadcast.stop_time() if broadcast is not None else None

    result = []
    for track in playlist:
        time_start = track.time_start
        if time_start < time_min:
            continue
        if time_max and time_start > time_max:
            break
        result.append(track)

    return result


async def get_new_order_pos() -> Optional[PlaylistItem]:
    playlist = await get_next()
    if not playlist or playlist[-1].is_order:  # если последний трек, что успеет проиграть, это заказ - вернем None
        return None

    for i, track in reversed(list(enumerate(playlist))):
        if track.is_order:  # т.к. заказы всегда в начале плейлиста, то нужен трек, следующий после последнего заказа
            return playlist[i + 1]
    return playlist[0]  # если нету заказов - вернуть самый первый трек в очереди


async def find_in_playlist_by_path(path: Union[str, Path]) -> List[PlaylistItem]:
    path = str(path)
    return [track for track in await _get_playlist() if track.filename == path]


async def get_free_time(broadcast):
    if broadcast.is_now():
        if (last_order := await get_new_order_pos()) is None:
            return 0
        last_order_start = last_order.time_start
    else:
        tracks_duration = await _calculate_tracks_duration(broadcast)
        last_order_start = broadcast.start_time() + timedelta(minutes=tracks_duration)

    t_d = (broadcast.stop_time() - last_order_start).total_seconds() / 60
    return max(.0, t_d)


#


async def _get_playlist() -> List[PlaylistItem]:
    if not (playlist := await radioboss.getplaylist2()):
        return []

    result = []
    for track in playlist['TRACK'][:100]:  # оптимизация: максимум 100 треков, покрывает самый длинный эфир, ~ 7 часов
        if not track['@STARTTIME']:  # если STARTTIME == "" скорее всего это не песня (либо она стартанет через >=сутки)
            continue

        track = PlaylistItem(
            title=track['@CASTTITLE'],
            time_start=get_by.time_to_datetime(datetime.strptime(track['@STARTTIME'], '%H:%M:%S').time()),  # set today
            filename=track['@FILENAME'],
            index=int(track['@INDEX']),
            is_order=str(others.PATHS['orders']) in track['@FILENAME']
        )
        result.append(track)

    return result


async def _calculate_tracks_duration(broadcast) -> float:
    return await _calculate_tracks_duration_(tuple(files.get_downloaded_tracks(broadcast.path())))


@other.my_lru(maxsize=7 * 7, ttl=60 * 60 * 12)
async def _calculate_tracks_duration_(files_):
    duration = 0
    for file in files_:
        if tag_info := await radioboss.readtag(file):
            duration += int(tag_info['TagInfo']['File']['@Duration'])
    return duration / 1000 / 60  # minutes
