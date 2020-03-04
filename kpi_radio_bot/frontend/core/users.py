"""Обработка действий обычных пользователей"""
from contextlib import suppress
from typing import Union

from aiogram import types, exceptions

from backend import music, files, playlist, Broadcast
from consts import texts, others, BOT
from frontend.frontend_utils import keyboards as kb
from utils import get_by, db


async def menu(message: types.Message):
    await message.answer(texts.MENU, reply_markup=kb.START)


# region playlist

async def playlist_now(message: types.Message):
    if not (broadcast := Broadcast.now()):
        return await message.answer(texts.SONG_NO_NOW, reply_markup=kb.WHAT_PLAYING)

    playback = [i if i else r'¯\_(ツ)_/¯' for i in await broadcast.get_now()]
    await message.answer(texts.WHAT_PLAYING.format(*playback), reply_markup=kb.WHAT_PLAYING)


async def playlist_next(query: types.CallbackQuery):
    if not (broadcast := Broadcast.now()):
        return await query.message.answer(texts.CHOOSE_DAY, reply_markup=kb.playlist_choose_day())
    await query.message.answer(await _get_playlist_text(broadcast),
                               reply_markup=kb.playlist_choose_time(broadcast.day))


async def playlist_choose_day(query: types.CallbackQuery):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_text(texts.CHOOSE_DAY, reply_markup=kb.playlist_choose_day())


async def playlist_choose_time(query: types.CallbackQuery, day: int):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_text(texts.CHOOSE_TIME.format(others.WEEK_DAYS[day]),
                                      reply_markup=kb.playlist_choose_time(day))


async def playlist_show(query: types.CallbackQuery, broadcast: Broadcast):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_text(await _get_playlist_text(broadcast),
                                      reply_markup=kb.playlist_choose_time(broadcast.day))


# endregion

async def timetable(message: types.Message):
    text = ''
    for day_num, day_name in {0: 'Будни', 6: 'Воскресенье'}.items():
        text += f"{day_name} \n"
        for break_num, (start, stop) in others.BROADCAST_TIMES[day_num].items():
            text += f"   {start} - {stop}   {others.TIMES[break_num]} \n"

    # todo
    # text += "До ближайшего эфира ..."

    await message.answer(text)


async def help_change(query: types.CallbackQuery, key: str):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_text(texts.HELP[key], reply_markup=kb.CHOICE_HELP)


async def notify_switch(message: types.Message):
    status = await db.notification_get(message.from_user.id)
    await db.notification_set(message.from_user.id, not status)
    text = "Уведомления <b>включены</b> \n /notify - выключить" if status else \
        "Уведомления <b>выключены</b> \n /notify - включить"
    await message.answer(text)


async def send_audio(chat: int, audio: Union[types.Audio, music.Audio]):
    if isinstance(audio, types.Audio):
        file = audio.file_id
        name = get_by.get_audio_name(audio)
        duration = audio.duration
    elif isinstance(audio, music.Audio):
        file = audio.download_url
        name = get_by.get_audio_name_(audio.artist, audio.title)
        duration = audio.duration
    else:
        raise Exception("шо ты мне передал блядь ебаный рот")

    bad_list = (
        (texts.BAD_ORDER_SHORT, duration < 60),
        (texts.BAD_ORDER_LONG, duration > 60 * 6),
        (texts.BAD_ORDER_BADWORDS, await music.check.is_contain_bad_words(name)),
        (texts.BAD_ORDER_ANIME, await music.check.is_anime(name)),
        (texts.BAD_ORDER_PERFORMER, music.check.is_bad_name(name)),
    )

    warnings = [text for text, b in bad_list if b]

    if warnings:
        text = texts.SOMETHING_BAD_IN_ORDER.format('\n'.join(warnings))
        await BOT.send_audio(chat, file, text, reply_markup=kb.BAD_ORDER_BUT_OK)
    else:
        await BOT.send_audio(chat, file, texts.CHOOSE_DAY, reply_markup=await kb.order_choose_day())


async def add_in_db(message: types.Message):
    await db.add(message.chat.id)


#


async def _get_playlist_text(broadcast: Broadcast) -> str:
    if broadcast.is_now():
        playback = await playlist.get_playlist_next()
        return '\n'.join([
            f"🕖<b>{track.time_start.strftime('%H:%M:%S')}</b> {track.title}"
            for track in playback[:10]
        ])
    else:
        name = f"<b>{broadcast.name}</b>\n"
        if not (playback := files.get_downloaded_tracks(broadcast.path)):
            return name + "❗️Еще ничего не заказали"

        text = name + '\n'.join([
            f"🕖<b>{i + 1}</b> {track.stem}"
            for i, track in enumerate(playback[:10])
        ])
        if len(playback) > 10:
            text += '\n<pre>   ...</pre>'
        return text
