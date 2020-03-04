from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple

import utils.get_by
from consts import others
from utils.lru import lru
from . import playlist, files, radioboss


class Broadcast:
    @lru()
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
        return utils.get_by.time_to_datetime(others.BROADCAST_TIMES_[self.day][self.num][0])

    def stop_time(self) -> datetime:
        return utils.get_by.time_to_datetime(others.BROADCAST_TIMES_[self.day][self.num][1])

    def is_today(self) -> bool:
        return self.day == datetime.now().weekday()

    def is_now(self) -> bool:
        return self.is_today() and self.start_time() < datetime.now() < self.stop_time()

    def is_will_be_play_today(self) -> bool:
        return self.is_today() and self.start_time() > datetime.now()

    def is_already_play_today(self) -> bool:
        return self.is_today() and self.stop_time() < datetime.now()

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

    async def get_now(self) -> Optional[List[str]]:
        if not self.is_now():
            return None
        return await playlist.get_now()

    async def get_playlist_next(self) -> Optional[playlist.PlayList]:
        if not self.is_now():
            return None
        return await playlist.get_bounded_playlist(datetime.now(), self.stop_time())

    async def get_new_order_pos(self) -> Optional[playlist.PlayList]:
        if not self.is_now():
            return None
        playlist_ = await self.get_playlist_next()
        return _get_new_order_pos(playlist_)

    async def get_free_time(self) -> float:
        if self.is_now():
            if (last_order := await self.get_new_order_pos()) is None:
                return 0
            last_order_start = last_order.time_start
        else:
            tracks_duration = await _calculate_tracks_duration(self)
            last_order_start = self.start_time() + timedelta(minutes=tracks_duration)

        t_d = (self.stop_time() - last_order_start).total_seconds() / 60
        return max(.0, t_d)

    def __str__(self):
        return self.name()

#


def _get_new_order_pos(playlist_: playlist.PlayList):
    if not playlist_ or playlist_[-1].is_order:  # если последний трек, что успеет проиграть, это заказ - вернем None
        return None

    for i, track in reversed(list(enumerate(playlist_))):
        if track.is_order:  # т.к. заказы всегда в начале плейлиста, то нужен трек, следующий после последнего заказа
            return playlist_[i + 1]
    return playlist_[0]  # если нету заказов - вернуть самый первый трек в очереди


async def _calculate_tracks_duration(broadcast: Broadcast) -> float:
    return await _calculate_tracks_duration_(tuple(files.get_downloaded_tracks(broadcast.path())))


@lru(maxsize=7 * 7, ttl=60 * 60 * 12)
async def _calculate_tracks_duration_(files_: Tuple[Path]) -> float:
    duration = 0
    for file in files_:
        if tag_info := await radioboss.readtag(file):
            duration += int(tag_info['TagInfo']['File']['@Duration'])
    return duration / 1000 / 60  # minutes
