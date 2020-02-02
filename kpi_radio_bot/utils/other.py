import os
from datetime import datetime
from urllib.parse import quote

from aiogram import types

import consts
from config import bot, HOST, ADMINS_CHAT_ID, PATH_SELF
from utils import music, broadcast


def get_audio_name(audio: types.Audio) -> str:
    return get_audio_name_(audio.performer, audio.title)


def get_audio_name_(performer, title) -> str:
    if performer and title:
        name = f'{performer} - {title}'
    elif not performer and not title:
        name = 'Названия нету :('
    else:
        name = title if title else performer
    name = ''.join(list(filter(lambda c: (c not in '/:*?"<>|'), name)))  # винда агрится на эти символы в пути
    return name


def get_audio_path(day, time, audio_name):
    return broadcast.get_broadcast_path(day, time) / (audio_name + '.mp3')


def get_user_name(user_obj: types.User) -> str:
    return get_user_name_(user_obj.id, user_obj.first_name)


def get_user_name_(id_, name):
    return '<a href="tg://user?id={0}">{1}</a>'.format(id_, name)


def get_user_from_entity(message):
    entities = message.caption_entities if message.audio or message.photo else message.entities
    if entities:
        return entities[0].user


async def gen_order_caption(day, time, user, audio_name=None, status=None, moder=None):
    async def get_bad_words_():
        res = await music.get_bad_words(audio_name)
        if not res:
            return ''

        title, bw = res
        return f'<a href="https://{HOST}/gettext/{quote(audio_name[:100])}">' \
               f'{"⚠" if bw else "🆗"} ({title})</a>  ' + ', '.join(bw)

    is_now = broadcast.is_this_broadcast_now(day, time)
    is_now_text = ' (сейчас!)' if is_now else ''
    user_name = get_user_name(user)
    text_datetime = consts.TIMES_NAME['week_days'][day] + ', ' + broadcast.get_broadcast_name(time)

    if not status:
        is_now_mark = '‼️' if is_now else '❗️'
        bad_words = await get_bad_words_()
        is_anime = '🅰️' if await music.is_anime(audio_name) else ''
        text = f'{is_now_mark} Новый заказ - {text_datetime} {is_now_text} от {user_name}\n{bad_words} {is_anime}'
    else:
        status_text = "✅Принят" if status != 'reject' else "❌Отклонен"
        moder_name = get_user_name(moder)
        text = f'Заказ: {text_datetime} {is_now_text} от {user_name} {status_text} ({moder_name})'

    return text, {'text_datetime': text_datetime, 'now': is_now}


async def is_moder(user_id):
    member = await bot.get_chat_member(ADMINS_CHAT_ID, user_id)
    return member and member.status in ('creator', 'administrator', 'member')


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


def reboot() -> None:
    os.system(rf'cmd.exe /C start {PATH_SELF}\\update.bat')
