"""Обработка действий обычных пользователей"""
from contextlib import suppress

from aiogram import types, exceptions

from bot.bot_utils import kb
from consts import texts, others
from player import Broadcast
from utils.db import Users


async def menu(message: types.Message):
    await message.answer(texts.MENU, reply_markup=kb.START)


# region playlist

async def playlist_now(message: types.Message):
    if not (broadcast := Broadcast.now()):
        return await message.answer(texts.PLAYLIST_NOW_NOTHING, reply_markup=kb.WHAT_PLAYING)

    playback = [i if i else r'¯\_(ツ)_/¯' for i in await broadcast.get_prev_now_next()]
    await message.answer(texts.PLAYLIST_NOW.format(*playback), reply_markup=kb.WHAT_PLAYING)


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
            text += f"   {start} - {stop}   {others.TIMES[break_num]}\n"

    if Broadcast.now():
        text += "\nЭфир прямо сейчас!"
    else:
        br = Broadcast.get_closest()
        text += f"\nБлижайший эфир - {'сегодня' if br.is_today() else others.WEEK_DAYS[br.day]}," \
                f" {br.start_time.strftime('%H:%M')}"

    await message.answer(text)


async def help_change(query: types.CallbackQuery, key: str):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_text(texts.HELP[key], reply_markup=kb.CHOICE_HELP)


async def notify_switch(message: types.Message):
    status = Users.notification_get(message.from_user.id)
    Users.notification_set(message.from_user.id, not status)
    text = "Уведомления <b>включены</b> \n /notify - выключить" if status else \
        "Уведомления <b>выключены</b> \n /notify - включить"
    await message.answer(text)


def add_in_db(message: types.Message):
    Users.add(message.chat.id)


#


async def _get_playlist_text(broadcast: Broadcast) -> str:
    name = f"<b>{broadcast.name}</b>\n"
    if not (pl := await broadcast.get_playlist_next()):
        return name + "❗️Еще ничего не заказали"

    return '\n'.join([
        f"🕖<b>{track.time_start.strftime('%H:%M:%S')}</b> {track.title}"
        for track in pl[:10]
    ]) + ('\n<pre>   ...</pre>' if len(pl) > 10 else '')
