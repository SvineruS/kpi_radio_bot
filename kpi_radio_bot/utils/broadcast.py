from datetime import datetime
from pathlib import Path
from typing import Union

import consts
from . import radioboss


def get_broadcast_num(dt: datetime = None) -> Union[bool, int]:
    if not dt:
        dt = datetime.now()

    day = dt.weekday()
    time = dt.hour * 60 + dt.minute

    for num, (time_start, time_stop) in consts.broadcast_times_[day].items():
        if time_start < time < time_stop:
            return num

    return False


def get_broadcast_name(time: int) -> str:
    return consts.times_name['times'][time]


def is_this_broadcast_now(day: int, time: int) -> bool:
    return day == datetime.today().weekday() and time is get_broadcast_num()


def is_broadcast_right_now() -> bool:
    return get_broadcast_num() is not False


async def get_broadcast_freetime(day: int, time: int) -> int:
    broadcast_start, broadcast_finish = consts.broadcast_times_[day][time]
    if is_this_broadcast_now(day, time):
        last_order = await radioboss.get_new_order_pos()
        if not last_order:
            return 0
        last_order_start = last_order['time_start'].hour * 60 + last_order['time_start'].minute
    else:
        tracks_duration = await calculate_tracks_duration(get_broadcast_path(day, time))
        last_order_start = broadcast_start + tracks_duration

    return max(0, broadcast_finish - last_order_start)


def get_broadcast_path(day: int, time: int = False) -> Path:
    t = consts.paths['orders']
    t /= f"D0{day+1}"
    if time is not False:  # так и должно быть
        t /= '{0} {1}'.format(time, consts.times_name['times'][time])
    return t


async def calculate_tracks_duration(path: Path) -> float:
    try:
        files = path.iterdir()
    except FileNotFoundError:
        return 0

    duration = 0
    for file in files:
        tags = await radioboss.radioboss_api(action='readtag', fn=file)
        duration += int(tags[0].attrib['Duration'])

    return duration / 1000 / 60  # minutes
