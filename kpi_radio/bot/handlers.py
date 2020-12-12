""" Хендлеры бота """
from contextlib import suppress

from aiogram import Dispatcher, types, executor, exceptions

from consts import texts, BOT
from bot import handlers_
from bot.bot_utils import communication, bind_filters, keyboards as kb
from player import Broadcast

DP = Dispatcher(BOT)
bind_filters(DP)

ALLOWED_FEEDBACK_TYPES = ['text', 'audio', 'photo', 'sticker']


# region commands
@DP.message_handler(commands=['start'], chat_type=types.ChatType.PRIVATE)
async def start_handler(message: types.Message):
    handlers_.users.add_in_db(message)
    await message.answer(texts.START)
    await handlers_.users.menu(message)


@DP.message_handler(commands=['cancel'], chat_type=types.ChatType.PRIVATE)
async def cancel(message: types.Message):
    await handlers_.users.menu(message)


@DP.message_handler(commands=['notify'], chat_type=types.ChatType.PRIVATE)
async def notify_handler(message: types.Message):
    await handlers_.users.notify_switch(message)


# endregion commands
# region replies
@DP.message_handler(lambda m: m.reply_to_message and communication.cache_is_set(m.reply_to_message.message_id),
                    content_types=ALLOWED_FEEDBACK_TYPES, chat_type=types.ChatType.PRIVATE)
@DP.message_handler(reply_to_bot_text=texts.FEEDBACK,
                    content_types=ALLOWED_FEEDBACK_TYPES, chat_type=types.ChatType.PRIVATE)
async def user_reply_to_feedback_or_moder_handler(message: types.Message):
    await communication.user_message(message)
    await message.answer(texts.FEEDBACK_THANKS, reply_markup=kb.START)


@DP.message_handler(reply_to_bot_text=texts.ORDER_CHOOSE_SONG, chat_type=types.ChatType.PRIVATE)
async def user_search_song_handler(message: types.Message):
    await handlers_.searching.search_audio(message)


# endregion replies


@DP.message_handler(content_types=['audio'], chat_type=types.ChatType.PRIVATE)
async def user_audio_handler(message: types.Message):
    return await handlers_.searching.sent_audio(message, message.audio)


# region buttons

@DP.message_handler(text=kb.MENU.WHAT_PLAYING, chat_type=types.ChatType.PRIVATE)
async def user_btn_what_playing_handler(message: types.Message):  # Кнопка 'Что играет?'
    await handlers_.users.playlist_now(message)


@DP.message_handler(text=kb.MENU.ORDER, chat_type=types.ChatType.PRIVATE)
async def user_btn_order_handler(message: types.Message):  # Кнопка 'Заказать песню'
    await message.answer(texts.ORDER_CHOOSE_SONG, reply_markup=types.ForceReply())
    await message.answer(texts.ORDER_INLINE_SEARCH, reply_markup=kb.ORDER_INLINE)


@DP.message_handler(text=kb.MENU.FEEDBACK, chat_type=types.ChatType.PRIVATE)
async def user_btn_feedback_handler(message: types.Message):  # Кнопка 'Обратная связь'
    await message.answer(texts.FEEDBACK, reply_markup=types.ForceReply())


@DP.message_handler(commands=['help'], chat_type=types.ChatType.PRIVATE)
@DP.message_handler(text=kb.MENU.HELP, chat_type=types.ChatType.PRIVATE)
async def user_btn_help_handler(message: types.Message):  # Кнопка 'Помощь'
    await message.answer(texts.HELP['start'], reply_markup=kb.CHOICE_HELP)


@DP.message_handler(text=kb.MENU.TIMETABLE, chat_type=types.ChatType.PRIVATE)
async def user_btn_timetable_handler(message: types.Message):  # Кнопка 'Расписание'
    await handlers_.users.timetable(message)


@DP.message_handler(chat_type=types.ChatType.PRIVATE)
async def user_other_handler(message: types.Message):  # Говорим пользователю что он дурак
    await message.answer_document("BQADAgADlgQAAsedmEuFDrds0XauthYE", texts.UNKNOWN_CMD, reply_markup=kb.START)


# endregion buttons
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


@DP.message_handler(content_types=ALLOWED_FEEDBACK_TYPES, reply_to_bot_text=None, admins_chat=True)
async def admins_reply_message_handler(message: types.Message):
    await communication.admin_message(message)


# endregion


# region callback
# region order

@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.DAY), cb_map=('day',))  # Выбрали день
async def query_handler_order_day(query, day):
    await handlers_.order.order_choose_time(query, day)


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.TIME), cb_map=('day', 'time'))  # Выбрали время
async def query_handler_order_time(query, day, time):
    await handlers_.order.order_make(query, Broadcast(day, time))


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.BACK))  # Кнопка назад при выборе времени
async def query_handler_order_back(query):
    await handlers_.order.order_choose_day(query)


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.CANCEL))  # Кнопка отмены при выборе дня
async def query_handler_order_cancel(query):
    await handlers_.order.order_cancel(query)


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.NOTIME), cb_map=('day', 'attempts'))  # Выбрал время но туда не влезет
async def query_handler_order_notime(query, day, attempts):
    await handlers_.order.order_no_time(query, day, attempts)


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.NOTIME), cb_map=('day', 'time', 'status'))  # Принять / отклонить
async def query_handler_order_moderate(query, day, time, status):
    await handlers_.order.admin_moderate(query, Broadcast(day, time), kb.STATUS(status))


@DP.callback_query_handler(cb=(kb.CB.ORDER, kb.CB.UNMODERATE), cb_map=('day', 'time', 'status'))  # Отменить выбор
async def query_handler_order_unmoderate(query, day, time, status):
    await handlers_.order.admin_unmoderate(query, Broadcast(day, time), kb.STATUS(status))


# endregion order
# region playlist


@DP.callback_query_handler(cb=(kb.CB.PLAYLIST, kb.CB.NEXT))  # Кнопка "что будет играть" в сообщении "что играет"
async def query_handler_playlist_next(query):
    await handlers_.users.playlist_next(query)


@DP.callback_query_handler(cb=(kb.CB.PLAYLIST, kb.CB.DAY), cb_map=('day', ))  # Выбор дня
async def query_handler_playlist_day(query, day):
    await handlers_.users.playlist_choose_time(query, day)


@DP.callback_query_handler(cb=(kb.CB.PLAYLIST, kb.CB.TIME), cb_map=('day', 'time'))  # Выбор времени
async def query_handler_playlist_time(query, day, time):
    await handlers_.users.playlist_show(query, Broadcast(day, time))


@DP.callback_query_handler(cb=(kb.CB.PLAYLIST, kb.CB.BACK))  # Кнопка назад при выборе времени
async def query_handler_playlist_back(query):
    await handlers_.users.playlist_choose_day(query)


@DP.callback_query_handler(cb=(kb.CB.PLAYLIST, kb.CB.MOVE), cb_map=('index', 'start_time'))  # Перемещения трека
async def query_handler_playlist_move(query, index, start_time):
    await handlers_.admins.playlist_move(query, index, start_time)


# endregion playlist
# region other


@DP.callback_query_handler(cb=(kb.CB.OTHER, kb.CB.HELP), cb_map=('key', ))  # Кнопка в сообщении с инструкцией
async def query_handler_other_help(query, key):
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
