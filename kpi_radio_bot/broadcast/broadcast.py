from datetime import datetime
from pathlib import Path
from typing import Optional

import consts


def get_broadcast_num(dt_: datetime = None) -> Optional[int]:
    if not dt_:
        dt_ = datetime.now()
    day, time = dt_.weekday(), dt_.time()

    for num, (time_start, time_stop) in consts.BROADCAST_TIMES_[day].items():
        if time_start < time < time_stop:
            return num
    return None


def get_broadcast_name(day: int = None, time: int = None) -> str:
    text = ''
    if day is not None:
        text += consts.TIMES_NAME['week_days'][day]
        if time is not None:
            text += ", "
    if time is not None:
        text += consts.TIMES_NAME['times'][time]
    return text


def get_broadcast_path(day: int, time: int = None) -> Path:
    path = consts.PATHS['orders']
    path /= f"D0{day + 1}"
    if time is not None:
        path /= '{0} {1}'.format(time, get_broadcast_name(time=time))
    return path


def is_this_broadcast_now(day: int, time: int) -> bool:
    return day == datetime.today().weekday() and time is get_broadcast_num()


def is_broadcast_right_now() -> bool:
    return get_broadcast_num() is not None
