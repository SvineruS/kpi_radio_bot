""" Хендлеры бота """
from contextlib import suppress
from typing import List

from aiogram import Dispatcher, types, executor, exceptions
from aiogram.dispatcher.handler import SkipHandler

import core
from config import BOT
from consts import keyboards, texts
from utils import bot_filters

DP = Dispatcher(BOT)
bot_filters.bind_filters(DP)


@DP.message_handler(commands=['start'], pm=True)
async def start_handler(message: types.Message):
    await core.users.add_in_db(message)
    await message.answer(texts.START)
    await core.users.menu(message)


@DP.message_handler(commands=['cancel'], pm=True)
async def cancel(message: types.Message):
    await core.users.menu(message)


@DP.message_handler(commands=['notify'], pm=True)
async def notify_handler(message: types.Message):
    await core.users.notify_switch(message)


@DP.message_handler(content_types=['text', 'audio', 'photo', 'sticker'], reply_to_bot=True, pm=True)
async def user_reply_message_handler(message: types.Message):
    reply_to = message.reply_to_message

    # Реплай на сообщение обратной связи или сообщение от модера
    if reply_to.text == texts.FEEDBACK or core.communication.cache_is_set(reply_to.message_id):
        await core.communication.user_message(message)
        return await message.answer(texts.FEEDBACK_THANKS, reply_markup=keyboards.START)

    # Ввод названия песни
    if reply_to.text == texts.ORDER_CHOOSE_SONG and not message.audio:
        return await core.search.search_audio(message)

    raise SkipHandler


@DP.message_handler(content_types=['audio'], pm=True)
async def user_audio_handler(message: types.Message):
    # Пользователь скинул аудио
    return await core.users.send_audio(message.chat.id, tg_audio=message.audio)


@DP.message_handler(pm=True)
async def user_buttons_handler(message: types.Message):
    # Кнопка 'Что играет?'
    if message.text == keyboards.MENU.WHAT_PLAYING:
        await core.users.playlist_now(message)

    # Кнопка 'Заказать песню'
    elif message.text == keyboards.MENU.ORDER:
        await message.answer(texts.ORDER_CHOOSE_SONG, reply_markup=types.ForceReply())
        await message.answer(texts.ORDER_INLINE_SEARCH, reply_markup=keyboards.ORDER_INLINE)

    # Кнопка 'Обратная связь'
    elif message.text == keyboards.MENU.FEEDBACK:
        await message.answer(texts.FEEDBACK, reply_markup=types.ForceReply())

    # Кнопка 'Помощь'
    elif message.text == keyboards.MENU.HELP or message.text == '/help':
        await message.answer(texts.HELP['start'], reply_markup=keyboards.CHOICE_HELP)

    # Кнопка 'Расписание'
    elif message.text == keyboards.MENU.TIMETABLE:
        await core.users.timetable(message)

    else:
        raise SkipHandler


@DP.message_handler(pm=True)
async def user_other_handler(message: types.Message):
    # Говорим пользователю что он дурак
    await message.answer_document("BQADAgADlgQAAsedmEuFDrds0XauthYE", texts.UNKNOWN_CMD, reply_markup=keyboards.START)


# region admins

@DP.message_handler(commands=['next'], admins_chat=True)
async def next_handler(message: types.Message):
    await core.admins.next_track(message)


@DP.message_handler(commands=['update'], admins_chat=True)
async def update_handler(message: types.Message):
    await core.admins.update(message)


@DP.message_handler(commands=['ban'], admins_chat=True)
async def ban_handler(message: types.Message):
    await core.admins.ban(message)


@DP.message_handler(commands=['vol', 'volume'], admins_chat=True)
async def volume_handler(message: types.Message):
    await core.admins.set_volume(message)


@DP.message_handler(commands=['stats'], admins_chat=True)
async def stats_handler(message: types.Message):
    await core.admins.get_stats(message)


@DP.message_handler(commands=['log'], admins_chat=True)
async def log_handler(message: types.Message):
    await core.admins.get_log(message)


@DP.message_handler(commands=['playlist'], admins_chat=True)
async def playlist_handler(message: types.Message):
    await core.admins.show_playlist_control(message)


@DP.message_handler(content_types=['text', 'audio', 'photo', 'sticker'], reply_to_bot=True, admins_chat=True)
async def admins_reply_message_handler(message: types.Message):
    return await core.communication.admin_message(message)


# endregion


@DP.callback_query_handler()
async def callback_query_handler(query: types.CallbackQuery):
    category, cmd, *params = keyboards.unparse(query.data)

    if category == keyboards.CB.ORDER:
        await order_callback_handler(query, cmd, params)

    elif category == keyboards.CB.PLAYLIST:
        await playlist_callback_handler(query, cmd, params)

    elif category == keyboards.CB.OTHER:
        await other_callback_handler(query, cmd, params)

    else:
        with suppress(exceptions.InvalidQueryID):
            await query.answer("Кнопка устарела")


@DP.inline_handler()
async def query_text_handler(inline_query: types.InlineQuery):
    await core.search.inline_search(inline_query)


async def order_callback_handler(query: types.CallbackQuery, cmd: keyboards.CB, params: list):
    # Выбрали день
    if cmd == keyboards.CB.DAY:
        *_, day = params
        await core.order.order_choose_time(query, day)

    # Выбрали время
    if cmd == keyboards.CB.TIME:
        *_, day, time = params
        await core.order.order_make(query, day, time)

    # Кнопка назад при выборе времени
    if cmd == keyboards.CB.BACK:
        await core.order.order_choose_day(query)

    # Кнопка отмены при выборе дня
    if cmd == keyboards.CB.CANCEL:
        await core.order.order_cancel(query)

    # Выбрал время но туда не влезет
    if cmd == keyboards.CB.NOTIME:
        *_, day, attempts = params
        await core.order.order_no_time(query, day, attempts)

    # Принять / отклонить
    if cmd == keyboards.CB.MODERATE:
        *_, day, time, status = params
        await core.order.admin_choice(query, day, time, keyboards.STATUS(status))

    # Отменить выбор
    if cmd == keyboards.CB.UNMODERATE:
        *_, day, time, status = params
        await core.order.admin_unchoice(query, day, time, status)


async def playlist_callback_handler(query: types.CallbackQuery, cmd: keyboards.CB, params: List[str]):
    # Кнопка "что будет играть" в сообщении "что играет"
    if cmd == keyboards.CB.NEXT:
        await core.users.playlist_next(query)

    # Выбор дня
    if cmd == keyboards.CB.DAY:
        *_, day = params
        await core.users.playlist_choose_time(query, day)

    # Выбор времени
    if cmd == keyboards.CB.TIME:
        *_, day, time = params
        await core.users.playlist_show(query, day, time)

    # Кнопка назад при выборе времени
    if cmd == keyboards.CB.BACK:
        await core.users.playlist_choose_day(query)

    # Админская кнопка перемещения трека в плейлисте
    if cmd == keyboards.CB.MOVE:
        *_, track_index, track_start_time = params
        await core.admins.playlist_move(query, track_index, track_start_time)


async def other_callback_handler(query: types.CallbackQuery, cmd: keyboards.CB, params: List[str]):
    # Кнопка в сообщении с инструкцией
    if cmd == keyboards.CB.HELP:
        *_, key = params
        await core.users.help_change(query, key)


if __name__ == '__main__':
    executor.start_polling(DP, skip_updates=True)
