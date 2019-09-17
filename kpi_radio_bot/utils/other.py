import csv
import os
from datetime import datetime
from urllib.parse import quote

from aiogram import types

import consts
from config import *
from utils import music, broadcast

from matplotlib import pyplot as plt
from matplotlib import figure
from collections import Counter


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
    return get_user_name_(user_obj.id, user_obj.first_name)


def get_user_name_(id_, name):
    return '<a href="tg://user?id={0}">{1}</a>'.format(id_, name)


async def gen_order_caption(day, time, user, audio_name=None, status=None, moder=None):
    async def get_bad_words():
        t = await music.search_text(audio_name) or ''
        bw = [word for word in consts.bad_words if word in t]
        if bw:
            return f'<a href="https://{HOST}/gettext/{quote(audio_name[0:100])}">⚠ </a>' + ', '.join(bw)
        return ''

    now = broadcast.is_broadcast_now(day, time)
    is_now_text = ' (сейчас!)' if now else ''
    user_name = get_user_name(user)
    text_datetime = consts.times_name['week_days'][day] + ', ' + broadcast.get_broadcast_name(time)

    if not status:
        is_now_mark = '‼️' if now else '❗️'
        bad_words = await get_bad_words()
        is_anime = '🅰️' if await music.is_anime(audio_name) else''
        text = f'{is_now_mark} Новый заказ - {text_datetime} {is_now_text} от {user_name}\n{bad_words} {is_anime}'
    else:
        status_text = "✅Принят" if status != 'reject' else "❌Отклонен"
        moder_name = get_user_name(moder)
        text = f'Заказ: {text_datetime} {is_now_text} от {user_name} {status_text} ({moder_name})'

    return text, {'text_datetime': text_datetime, 'now': now}


def case_by_num(num: int, c1: str, c2: str, c3: str) -> str:
    if 11 <= num <= 14:
        return c3
    if num % 10 == 1:
        return c1
    if 2 <= num % 10 <= 4:
        return c2
    return c3


def song_format(playback):
    text = [
        f"🕖<b>{datetime.strftime(track['time_start'], '%H:%M:%S')}</b> {track['title']}"
        for track in playback
    ]
    return '\n'.join(text)


def add_moder_stats(*data):
    with open(PATH_STUFF / 'stats.csv', "a", newline='', encoding='utf-8-sig') as csv_file:
        writer = csv.writer(csv_file, delimiter=',')
        writer.writerow(data)


def gen_stats_graph(n_days=7):
    with open(PATH_STUFF / 'stats.csv', encoding='utf-8-sig') as file:
        records = list(csv.reader(file, delimiter=','))

    last_n_days = set(record[-1][:10] for record in records)  # гениальное изобретение by hatomist
    last_n_days = sorted(list(last_n_days))[-n_days:]  # лист с последними n_days встречающимися датами (yyyy-mm-dd)

    cnt = Counter()
    for record in records:
        if record[-1][:10] in last_n_days:
            cnt[record[1]] += 1

    fig: figure.Figure = plt.figure(figsize=(12, 10))
    plt.barh(list(cnt.keys()), list(cnt.values()), height=0.8)
    plt.savefig(PATH_STUFF / 'stats.png', dpi=300)


def reboot() -> None:
    os.system(rf'cmd.exe /C start {PATH_SELF}\\update.bat')


