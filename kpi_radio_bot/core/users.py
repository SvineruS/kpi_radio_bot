"""Обработка действий обычных пользователей"""

from datetime import datetime

from aiogram.utils import exceptions

from broadcast import broadcast, playlist
from config import BOT
from consts import BROADCAST_TIMES, texts, keyboards
from utils import get_by, db, music


async def menu(message):
    await BOT.send_message(message.chat.id, texts.MENU, reply_markup=keyboards.START)


async def song_now(message):
    playback = await playlist.get_now()
    if not broadcast.is_broadcast_right_now() or not playback:
        return await BOT.send_message(message.chat.id, texts.SONG_NO_NOW, reply_markup=keyboards.WHAT_PLAYING)
    await BOT.send_message(message.chat.id, texts.WHAT_PLAYING.format(*playback), reply_markup=keyboards.WHAT_PLAYING)


async def song_next(query):
    playback = await playlist.get_next()
    if not playback:
        return await BOT.send_message(query.message.chat.id, texts.SONG_NO_NEXT)
    await BOT.send_message(query.message.chat.id, _song_format(playback[:5]))


async def timetable(message):
    text = ''
    for day_num, day_name in {0: 'Будни', 6: 'Воскресенье'}.items():
        text += f"{day_name} \n"
        for break_num, (start, stop) in BROADCAST_TIMES[day_num].items():
            text += f"   {start} - {stop}   {broadcast.get_broadcast_name(break_num)} \n"

    # todo
    # text += "До ближайшего эфира ..."

    await BOT.send_message(message.chat.id, text)


async def help_change(query, key):
    try:
        await BOT.edit_message_text(texts.HELP[key], query.message.chat.id, query.message.message_id,
                                    reply_markup=keyboards.CHOICE_HELP)
    except exceptions.MessageNotModified:
        pass


async def notify_switch(message):
    status = await db.notification_get(message.from_user.id)
    await db.notification_set(message.from_user.id, not status)
    text = "Уведомления <b>включены</b> \n /notify - выключить" if status else \
        "Уведомления <b>выключены</b> \n /notify - включить"
    await BOT.send_message(message.chat.id, text)


async def send_audio(chat, tg_audio=None, api_audio=None):
    if tg_audio:
        file = tg_audio.file_id
        name = get_by.get_audio_name(tg_audio)
        duration = tg_audio.duration
    elif api_audio:
        file = music.get_download_url(api_audio['url'], api_audio['artist'], api_audio['title'])
        name = get_by.get_audio_name_(api_audio['artist'], api_audio['title'])
        duration = int(api_audio['duration'])
    else:
        raise Exception("шо ты мне передал блядь ебаный рот")

    bad_list = (
        (texts.BAD_ORDER_SHORT, duration < 60),
        (texts.BAD_ORDER_LONG, duration > 60 * 6),
        (texts.BAD_ORDER_BADWORDS, await music.is_contain_bad_words(name)),
        (texts.BAD_ORDER_ANIME, await music.is_anime(name)),
        (texts.BAD_ORDER_PERFORMER, music.is_bad_name(name)),
    )

    warnings = list(text for text, b in bad_list if b)

    if warnings:
        text = texts.SOMETHING_BAD_IN_ORDER.format('\n'.join(warnings))
        await BOT.send_audio(chat, file, text, reply_markup=keyboards.BAD_ORDER_BUT_OK)
    else:
        await BOT.send_audio(chat, file, texts.ORDER_CHOOSE_DAY, reply_markup=await keyboards.choice_day())


async def add_in_db(message):
    await db.add(message.chat.id)


#

def _song_format(playback):
    return '\n'.join([
        f"🕖<b>{datetime.strftime(track['time_start'], '%H:%M:%S')}</b> {track['title']}"
        for track in playback
    ])
