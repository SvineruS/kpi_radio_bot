"""Обработка действий обычных пользователей"""
from datetime import datetime

from aiogram.utils import exceptions

from broadcast import broadcast, playlist
from config import BOT
from consts import BROADCAST_TIMES, texts, keyboards, TIMES_NAME
from utils import get_by, db, music, files


async def menu(message):
    await BOT.send_message(message.chat.id, texts.MENU, reply_markup=keyboards.START)


async def playlist_now(message):
    playback = await playlist.get_now()
    if not playback or not broadcast.is_broadcast_right_now():
        return await BOT.send_message(message.chat.id, texts.SONG_NO_NOW, reply_markup=keyboards.WHAT_PLAYING)
    playback = [i if i else r'¯\_(ツ)_/¯' for i in playback]
    await BOT.send_message(message.chat.id, texts.WHAT_PLAYING.format(*playback), reply_markup=keyboards.WHAT_PLAYING)


async def playlist_next(query):
    if broadcast.is_broadcast_right_now():
        text = _get_playlist()
        day = datetime.today().weekday()
        await BOT.send_message(query.message.chat.id, text, reply_markup=keyboards.playlist_choose_time(day))
    else:
        text = texts.CHOOSE_DAY
        await BOT.send_message(query.message.chat.id, text, reply_markup=keyboards.playlist_choose_day())


async def playlist_choose_day(query):
    await BOT.edit_message_text(
        texts.CHOOSE_DAY, query.message.chat.id, query.message.message_id,
        reply_markup=keyboards.playlist_choose_day()
    )


async def playlist_choose_time(query, day):
    await BOT.edit_message_text(
        texts.CHOOSE_TIME.format(TIMES_NAME['week_days'][day]),
        query.message.chat.id, query.message.message_id,
        reply_markup=keyboards.playlist_choose_time(day)
    )


async def playlist_show(query, day, time):
    try:
        await BOT.edit_message_text(
            await _get_playlist(day, time),
            query.message.chat.id, query.message.message_id,
            reply_markup=keyboards.playlist_choose_time(day)
        )
    except exceptions.MessageNotModified:
        pass


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
        await BOT.send_audio(chat, file, texts.CHOOSE_DAY, reply_markup=await keyboards.order_choice_day())


async def add_in_db(message):
    await db.add(message.chat.id)


#


async def _get_playlist(day=None, time=None):
    if day is None or broadcast.is_this_broadcast_now(day, time):
        playback = await playlist.get_next()
        return '\n'.join([
            f"🕖<b>{track.time_start.strftime('%H:%M:%S')}</b> {track.title}"
            for track in playback[:10]
        ])
    else:
        playback = files.get_downloaded_tracks(day, time)
        if not playback:
            return "❗️Еще ничего не заказали"
        return '\n'.join([
            f"🕖<b>{i}</b> {track.name}"
            for i, track in enumerate(playback[:10])
        ])
