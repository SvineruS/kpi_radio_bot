from datetime import datetime
from pathlib import Path
from typing import Union

import consts


def get_broadcast_num(dt_: datetime = None) -> Union[bool, int]:
    if not dt_:
        dt_ = datetime.now()

    day, time = dt_.weekday(), dt_.time()

    for num, (time_start, time_stop) in consts.BROADCAST_TIMES_[day].items():
        if time_start < time < time_stop:
            return num

    return False


def get_broadcast_name(time: int) -> str:
    return consts.TIMES_NAME['times'][time]


def get_broadcast_path(day: int, time: int = False) -> Path:
    path = consts.PATHS['orders']
    path /= f"D0{day + 1}"
    if time is not False:  # так и должно быть
        path /= '{0} {1}'.format(time, consts.TIMES_NAME['times'][time])
    return path


def is_this_broadcast_now(day: int, time: int) -> bool:
    return day == datetime.today().weekday() and time is get_broadcast_num()


def is_broadcast_right_now() -> bool:
    return get_broadcast_num() is not False
