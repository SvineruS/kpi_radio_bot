"""Обработка действий обычных пользователей"""
from contextlib import suppress

from aiogram import types, exceptions

from bot.bot_utils import kb
from consts import texts, others
from player import Ether, Broadcast
from utils.db import Users


async def menu(message: types.Message):
    await message.answer(texts.MENU, reply_markup=kb.START)


# region playlist

async def playlist_now(message: types.Message):
    ether = Ether.now()
    if not ether:
        print(Ether.ALL)
        return await message.answer(texts.PLAYLIST_NOW_NOTHING, reply_markup=kb.WHAT_PLAYING)

    playback = [str(i) if i else r'¯\_(ツ)_/¯' for i in await Broadcast(ether).get_playback()]
    await message.answer(texts.PLAYLIST_NOW.format(*playback), reply_markup=kb.WHAT_PLAYING)


async def playlist_next(query: types.CallbackQuery):
    if not (ether := Ether.now()):
        return await query.message.answer(texts.CHOOSE_DAY, reply_markup=kb.playlist_choose_day())
    await query.message.answer(await _get_playlist_text(ether), reply_markup=kb.playlist_choose_time(ether.day))


async def playlist_choose_day(query: types.CallbackQuery):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_text(texts.CHOOSE_DAY, reply_markup=kb.playlist_choose_day())


async def playlist_choose_time(query: types.CallbackQuery, day: int):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_text(texts.CHOOSE_TIME.format(others.WEEK_DAYS[day]),
                                      reply_markup=kb.playlist_choose_time(day))


async def playlist_show(query: types.CallbackQuery, ether: Ether):
    with suppress(exceptions.MessageNotModified):
        return await query.message.edit_text(await _get_playlist_text(ether),
                                             reply_markup=kb.playlist_choose_time(ether.day))
    await query.answer()


# endregion

async def timetable(message: types.Message):
    text = ''
    for day_num, day_name in others.TIMETABLE_SECTIONS.items():
        text += f"{day_name} \n"
        for break_num, (start, stop) in others.ETHER_TIMES[day_num].items():
            text += texts.TIMETABLE_ITEM.format(start=start, stop=stop, ether_name=others.ETHER_NAMES[break_num])

    closest_ether = Ether.get_closest()
    if closest_ether.is_now():
        text += "\n" + texts.TIMETABLE_ETHER_NOW
    else:
        text += "\n" + texts.TIMETABLE_ETHER_CLOSEST.format(
            when_day=others.NEXT_DAYS[0] if closest_ether.is_today() else others.WEEK_DAYS[closest_ether.day],
            when_time=closest_ether.start_time.strftime('%H:%M')
        )

    await message.answer(text)


async def help_change(query: types.CallbackQuery, key: str):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_text(texts.HELP[key], reply_markup=kb.CHOICE_HELP)


async def notify_switch(message: types.Message):
    status = Users.notification_get(message.from_user.id)
    Users.notification_set(message.from_user.id, not status)
    await message.answer(texts.ORDER_NOTIFY_STATUS[status])


def add_in_db(message: types.Message):
    Users.add(message.chat.id)


#


async def _get_playlist_text(ether: Ether) -> str:
    name = f"<b>{ether.name}</b>\n"
    if not (pl := await Broadcast(ether).get_next_tracklist()):
        return name + texts.PLAYLIST_EMPTY

    return name + '\n'.join([
        texts.PLAYLIST_ITEM.format(start_time=track.start_time.strftime('%H:%M:%S'), track_name=str(track))
        for track in pl[:10]
    ]) + ('\n<pre>   ...</pre>' if len(pl) > 10 else '')
