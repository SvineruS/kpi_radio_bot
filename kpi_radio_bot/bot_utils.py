import logging
import os
import shutil
from datetime import datetime
from typing import Union

from aiogram import types

import consts
import playlist_api
from config import *


# TODO переименовать все нахуй, что это блядь такое
def get_music_path(day: int, time: int = False) -> Path:
    t = consts.paths['orders']
    t /= '0{0}_{1}'.format(day + 1, consts.times_name['week_days'][day])

    if time is False:    # сука 0 считается как False
        return t

    if day == 6:         # В воскресенье только утренний(0) и вечерний эфир(5)
        t /= consts.times_name['times'][time]
    elif time < 5:       # До вечернего эфира
        t /= '{0}.{1}'.format(time, consts.times_name['times'][time])
    else:                # Вечерний эфир
        t /= '({0}){1}'.format(day + 1, consts.times_name['week_days'][day])

    return t


def get_break_num(time: datetime = None) -> Union[bool, int]:
    if not time:
        time = datetime.now()
        day = datetime.today().weekday()
    else:
        day = time.weekday()
    time = time.hour * 60 + time.minute

    times = consts.broadcast_times_['sunday' if day == 6 else 'elseday']
    for num, (time_start, time_stop) in times.items():
        if time_start < time < time_stop:
            return num

    return False


def get_break_name(time: int) -> str:
    return consts.times_name['times'][time]


def is_break_now(day: int, time: int) -> bool:
    return day == datetime.today().weekday() and time is get_break_num()


async def order_time_left(day, time):
    break_start, break_finish = consts.broadcast_times_['sunday' if day == 6 else 'elseday'][time]
    if is_break_now(day, time):
        last_order = await playlist_api.get_new_order_pos()
        if not last_order:
            return 0
        start = last_order['time_start'].hour * 60 + last_order['time_start'].minute
    else:
        try:
            music_count = len(list(get_music_path(day, time).iterdir()))
        except FileNotFoundError:
            music_count = 0
        start = break_start + music_count * 3   # 3 минуты - средняя длина музычки

    return max(0, break_finish - start)


def get_audio_name(audio: types.Audio) -> str:
    if audio.performer and audio.title:
        name = f'{audio.performer} - {audio.title}'
    elif not audio.performer and not audio.title:
        name = 'Названия нету :('
    else:
        name = audio.title if audio.title else audio.performer
    name = ''.join(list(filter(lambda c: (c not in '/:*?"<>|'), name)))  # винда агрится на эти символы в пути
    return name


def get_user_name(user_obj: types.User) -> str:
    return '<a href="tg://user?id={0}">{1}</a>'.format(user_obj.id, user_obj.first_name)


def case_by_num(num: int, c1: str, c2: str, c3: str) -> str:
    if 11 <= num <= 14:
        return c3
    if num % 10 == 1:
        return c1
    if 2 <= num % 10 <= 4:
        return c2
    return c3


def create_dirs(to: Union[str, Path]) -> None:
    dirname = os.path.dirname(to)
    if not os.path.exists(dirname):
        os.makedirs(dirname)


def delete_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        path.unlink()
    except Exception as ex:
        logging.error(f'delete file: {ex} {path}')


async def delete_old_orders() -> None:
    wd = datetime.now().weekday()
    src = str(get_music_path(wd))       # заказы
    dst = str(consts.paths['archive'])  # архив

    if not os.path.exists(dst):
        os.makedirs(dst)

    for src_dir, dirs, files in os.walk(src):
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst, file_)
            try:
                shutil.move(src_file, dst_file)
            except Exception as ex:
                logging.error(f'move file: {ex} {src_file}')


def check_bad_words(text: str) -> str:
    answ = []
    for word in consts.bad_words:
        if word in text:
            answ.append(word)

    if answ:
        return "Нашел это: " + ' '.join(answ)
    return "Все ок вродь"


def write_sender_tag(path, user_obj):
    name = get_user_name(user_obj)
    playlist_api.write_tag(path, name)


def read_sender_tag(path):
    return playlist_api.read_tag(path)


def song_format(playback):
    text = [
        f"🕖<b>{datetime.strftime(track['time_start'], '%H:%M:%S')}</b> {track['title']}"
        for track in playback
    ]
    return '\n'.join(text)


def reboot() -> None:
    os.system(rf'cmd.exe /C start {PATH_SELF}\\update.bat')

