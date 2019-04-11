import logging
import os
import shutil
import xml.etree.ElementTree as Etree
from aiogram import types
from datetime import datetime
from music_api import radioboss_api
from base64 import b64decode, b64encode
from config import *
from typing import Union
import consts


def get_music_path(day: int, time: int = False) -> Path:
    t = consts.paths['orders']
    t /= '0{0}_{1}'.format(day + 1, consts.TEXT['days1'][day])

    if time is False:    # сука 0 считается как False
        return t

    if day == 6:         # В воскресенье только утренний(0) и вечерний эфир(5)
        t /= consts.TEXT['times'][time]
    elif time < 5:       # До вечернего эфира
        t /= '{0}.{1}'.format(time, consts.TEXT['times'][time])
    else:                # Вечерний эфир
        t /= '({0}){1}'.format(day + 1, consts.TEXT['days1'][day])

    return t


def get_break_num(time: datetime = None) -> Union[bool, int]:
    if not time:
        time = datetime.now()
        day = datetime.today().weekday()
    else:
        day = time.weekday()
    time = time.hour * 60 + time.minute

    if time > 22 * 60 or time < 7 * 60:     # точно не время эфира
        return False

    if day == 6:                            # Воскресенье
        if time > 18 * 60:                  # Вечерний эфир
            return 5
        if time > 11 * 60 + 15:             # Утренний эфир
            return 0
        return False                        # Не эфир

    if time <= 8 * 60 + 30:                 # Утренний эфир
        return 0
    if time >= 17 * 60 + 50:                # Вечерний эфир
        return 5

    for i in range(4):                      # Перерыв.  10:05 + пара * i   (10:05 - начало 1 перерыва)
        if 0 <= time - (10 * 60 + 5 + i * 115) <= 20:
            return i + 1

    return False                            # Не эфир


def get_break_name(time: int) -> str:
    return consts.TEXT['times'][time]


def is_break_now(day: int, time: int) -> bool:
    return day == datetime.today().weekday() and time is get_break_num()


def get_audio_name(audio: types.Audio) -> str:
    if not audio.performer and not audio.title:
        name = 'Названия нету :('
    else:
        name = ' - '.join([str(audio.performer), str(audio.title)])
    name = ''.join(list(filter(lambda c: (c not in '/:*?"<>|'), name)))  # винда агрится на эти символы в пути
    return name


def get_user_name(user_obj: types.User) -> str:
    return '<a href="tg://user?id={0}">{1}</a>'.format(user_obj.id, user_obj.first_name)


def case_by_num(num, c1, c2, c3):
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
    if os.path.isfile(to):
        return


def delete_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        path.unlink()
    except Exception as ex:
        logging.error(f'delete file: {ex} {path}')


async def write_sender_tag(path: Path, user_obj: types.User) -> None:
    tags = await radioboss_api(action='readtag', fn=path)
    name = get_user_name(user_obj)
    name = b64encode(name.encode('utf-8')).decode('utf-8')
    tags[0].attrib['Comment'] = name
    xmlstr = Etree.tostring(tags, encoding='utf8', method='xml').decode('utf-8')
    await radioboss_api(action='writetag', fn=path, data=xmlstr)


async def read_sender_tag(path: Path) -> Union[bool, str]:
    tags = await radioboss_api(action='readtag', fn=path)
    name = tags[0].attrib['Comment']
    try:
        name = b64decode(name).decode('utf-8')
    except:
        return False
    return name


async def delete_old_orders() -> None:
    wd = datetime.now().weekday()
    src = str(get_music_path(wd))  # заказы
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
    if 'Ошибка' in text:  # хуевый мув, да. срабатывает на "ошибка поиска"
        return text

    bad_words = ['пизд',
                 'бля',
                 'хуй', 'хуя', 'хуи', 'хуе',
                 'ебать', 'еби', 'ебло', 'ебля', 'ебуч',
                 'долбо',
                 'дрочит',
                 'мудак', 'мудило',
                 'пидор', 'пидар',
                 'сука', 'суку',
                 'гандон',
                 'fuck']

    answ = []
    for word in bad_words:
        if word in text:
            answ.append(word)

    if not answ:
        return "Все ок вродь"
    else:
        return "Нашел это: " + ' '.join(answ)


def reboot() -> None:
    os.system(r'cmd.exe /C start ' + os.getcwd() + '\\update.bat')

