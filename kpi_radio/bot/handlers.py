""" Хендлеры бота """
from contextlib import suppress

from aiogram import Dispatcher, types, executor, exceptions
from aiogram.dispatcher.handler import SkipHandler

from consts import texts, BOT
from bot import handlers_
from bot.bot_utils import communication, bind_filters, keyboards as kb
from player import Broadcast

DP = Dispatcher(BOT)
bind_filters(DP)


@DP.message_handler(commands=['start'], chat_type=types.ChatType.PRIVATE)
async def start_handler(message: types.Message):
    await handlers_.users.add_in_db(message)
    await message.answer(texts.START)
    await handlers_.users.menu(message)


@DP.message_handler(commands=['cancel'], chat_type=types.ChatType.PRIVATE)
async def cancel(message: types.Message):
    await handlers_.users.menu(message)


@DP.message_handler(commands=['notify'], chat_type=types.ChatType.PRIVATE)
async def notify_handler(message: types.Message):
    await handlers_.users.notify_switch(message)


@DP.message_handler(content_types=['text', 'audio', 'photo', 'sticker'],
                    reply_to_bot=True, chat_type=types.ChatType.PRIVATE)
async def user_reply_message_handler(message: types.Message):
    reply_to = message.reply_to_message

    # Реплай на сообщение обратной связи или сообщение от модера
    if reply_to.text == texts.FEEDBACK or communication.cache_is_set(reply_to.message_id):
        await communication.user_message(message)
        return await message.answer(texts.FEEDBACK_THANKS, reply_markup=kb.START)

    # Ввод названия песни
    if reply_to.text == texts.ORDER_CHOOSE_SONG and not message.audio:
        return await handlers_.searching.search_audio(message)

    raise SkipHandler


@DP.message_handler(content_types=['audio'], chat_type=types.ChatType.PRIVATE)
async def user_audio_handler(message: types.Message):
    # Пользователь скинул аудио
    return await handlers_.searching.sent_audio(message, message.audio)


@DP.message_handler(chat_type=types.ChatType.PRIVATE)
async def user_buttons_handler(message: types.Message):
    # Кнопка 'Что играет?'
    if message.text == kb.MENU.WHAT_PLAYING:
        await handlers_.users.playlist_now(message)

    # Кнопка 'Заказать песню'
    elif message.text == kb.MENU.ORDER:
        await message.answer(texts.ORDER_CHOOSE_SONG, reply_markup=types.ForceReply())
        await message.answer(texts.ORDER_INLINE_SEARCH, reply_markup=kb.ORDER_INLINE)

    # Кнопка 'Обратная связь'
    elif message.text == kb.MENU.FEEDBACK:
        await message.answer(texts.FEEDBACK, reply_markup=types.ForceReply())

    # Кнопка 'Помощь'
    elif message.text == kb.MENU.HELP or message.text == '/help':
        await message.answer(texts.HELP['start'], reply_markup=kb.CHOICE_HELP)

    # Кнопка 'Расписание'
    elif message.text == kb.MENU.TIMETABLE:
        await handlers_.users.timetable(message)

    else:
        raise SkipHandler


@DP.message_handler(chat_type=types.ChatType.PRIVATE)
async def user_other_handler(message: types.Message):
    # Говорим пользователю что он дурак
    await message.answer_document("BQADAgADlgQAAsedmEuFDrds0XauthYE", texts.UNKNOWN_CMD, reply_markup=kb.START)


# region admins

@DP.message_handler(commands=['next'], admins_chat=True)
async def next_handler(message: types.Message):
    await handlers_.admins.next_track(message)


@DP.message_handler(commands=['update'], admins_chat=True)
async def update_handler(message: types.Message):
    await handlers_.admins.update(message)


@DP.message_handler(commands=['ban'], admins_chat=True)
async def ban_handler(message: types.Message):
    await handlers_.admins.ban(message)


@DP.message_handler(commands=['vol', 'volume'], admins_chat=True)
async def volume_handler(message: types.Message):
    await handlers_.admins.set_volume(message)


@DP.message_handler(commands=['stats'], admins_chat=True)
async def stats_handler(message: types.Message):
    await handlers_.admins.get_stats(message)


@DP.message_handler(commands=['log'], admins_chat=True)
async def log_handler(message: types.Message):
    await handlers_.admins.get_log(message)


@DP.message_handler(commands=['playlist'], admins_chat=True)
async def playlist_handler(message: types.Message):
    await handlers_.admins.show_playlist_control(message)


@DP.message_handler(content_types=['text', 'audio', 'photo', 'sticker'], reply_to_bot=True, admins_chat=True)
async def admins_reply_message_handler(message: types.Message):
    return await communication.admin_message(message)


# endregion


# region callback
# region order

@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.DAY))  # Выбрали день
async def query_handler_order_day(query, json_data):
    day, *_ = json_data
    await handlers_.order.order_choose_time(query, day)


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.TIME))  # Выбрали время
async def query_handler_order_time(query, json_data):
    day, time, *_ = json_data
    await handlers_.order.order_make(query, Broadcast(day, time))


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.BACK))  # Кнопка назад при выборе времени
async def query_handler_order_back(query):
    await handlers_.order.order_choose_day(query)


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.CANCEL))  # Кнопка отмены при выборе дня
async def query_handler_order_cancel(query):
    await handlers_.order.order_cancel(query)


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.NOTIME))  # Выбрал время но туда не влезет
async def query_handler_order_notime(query, json_data):
    day, attempts, *_ = json_data
    await handlers_.order.order_no_time(query, day, attempts)


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.NOTIME))  # Принять / отклонить
async def query_handler_order_moderate(query, json_data):
    day, time, status, *_ = json_data
    await handlers_.order.admin_moderate(query, Broadcast(day, time), kb.STATUS(status))


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.UNMODERATE))  # Отменить выбор
async def query_handler_order_unmoderate(query, json_data):
    day, time, status, *_ = json_data
    await handlers_.order.admin_unmoderate(query, Broadcast(day, time), kb.STATUS(status))

# endregion order
# region playlist


@DP.callback_query_handler(cb=(kb.CB.PLAYLIST, kb.CB.NEXT))  # Кнопка "что будет играть" в сообщении "что играет"
async def query_handler_playlist_next(query):
    await handlers_.users.playlist_next(query)


@DP.callback_query_handler(cb=(kb.CB.PLAYLIST, kb.CB.DAY))  # Выбор дня
async def query_handler_playlist_day(query, json_data):
    day, *_ = json_data
    await handlers_.users.playlist_choose_time(query, day)


@DP.callback_query_handler(cb=(kb.CB.PLAYLIST, kb.CB.DAY))  # Выбор времени
async def query_handler_playlist_time(query, json_data):
    day, time, *_ = json_data
    await handlers_.users.playlist_show(query, Broadcast(day, time))


@DP.callback_query_handler(cb=(kb.CB.PLAYLIST, kb.CB.BACK))  # Кнопка назад при выборе времени
async def query_handler_playlist_back(query):
    await handlers_.users.playlist_choose_day(query)


@DP.callback_query_handler(cb=(kb.CB.PLAYLIST, kb.CB.MOVE))  # Админская кнопка перемещения трека в плейлисте
async def query_handler_playlist_move(query, json_data):
    track_index, track_start_time, *_ = json_data
    await handlers_.admins.playlist_move(query, track_index, track_start_time)

# endregion playlist
# region other


@DP.callback_query_handler(cb=(kb.CB.OTHER, kb.CB.HELP))  # Кнопка в сообщении с инструкцией
async def query_handler_other_help(query, json_data):
    key, *_ = json_data
    await handlers_.users.help_change(query, key)


@DP.callback_query_handler()  # Какая то левая кнопка
async def query_handler_other(query):
    with suppress(exceptions.InvalidQueryID):
        await query.answer()

# endregion other
# endregion callback


@DP.inline_handler()
async def inline_query_handler(inline_query: types.InlineQuery):
    await handlers_.searching.inline_search(inline_query)


if __name__ == '__main__':
    executor.start_polling(DP, skip_updates=True)
