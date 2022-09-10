""" Хендлеры бота """
from contextlib import suppress

from aiogram import types, exceptions

from bot import handlers_
from bot.bot_utils import communication, kb
from consts import texts
from player import Ether

ALLOWED_FEEDBACK_TYPES = ['text', 'audio', 'photo', 'sticker']


def register_handlers(dp):
    # region commands
    @dp.message_handler(commands=['start'], chat_type=types.ChatType.PRIVATE)
    async def start_handler(message: types.Message):
        handlers_.users.add_in_db(message)
        await message.answer(texts.START)
        await handlers_.users.menu(message)

    @dp.message_handler(commands=['cancel'], chat_type=types.ChatType.PRIVATE)
    async def cancel(message: types.Message):
        await handlers_.users.menu(message)

    @dp.message_handler(commands=['notify'], chat_type=types.ChatType.PRIVATE)
    async def notify_handler(message: types.Message):
        await handlers_.users.notify_switch(message)

    # region admins

    @dp.message_handler(commands=['next'], admins_chat=True)
    async def next_handler(message: types.Message):
        await handlers_.admins.next_track(message)

    @dp.message_handler(commands=['ban'], admins_chat=True)
    async def ban_handler(message: types.Message):
        await handlers_.admins.ban(message)

    @dp.message_handler(commands=['vol', 'volume'], admins_chat=True)
    async def volume_handler(message: types.Message):
        await handlers_.admins.set_volume(message)

    @dp.message_handler(commands=['stats'], admins_chat=True)
    async def stats_handler(message: types.Message):
        await handlers_.admins.get_stats(message)

    @dp.message_handler(commands=['log'], admins_chat=True)
    async def log_handler(message: types.Message):
        await handlers_.admins.get_log(message)

    @dp.message_handler(commands=['playlist'], admins_chat=True)
    async def playlist_handler(message: types.Message):
        await handlers_.admins.show_playlist_control(message)

    # endregion admins
    # endregion commands

    # region replies

    @dp.message_handler(lambda m: m.reply_to_message and communication.cache_is_set(m.reply_to_message.message_id),
                        content_types=ALLOWED_FEEDBACK_TYPES, chat_type=types.ChatType.PRIVATE)
    @dp.message_handler(reply_to_bot_text=texts.FEEDBACK,
                        content_types=ALLOWED_FEEDBACK_TYPES, chat_type=types.ChatType.PRIVATE)
    async def user_reply_to_feedback_or_moder_handler(message: types.Message):
        await communication.user_message(message)
        await message.answer(texts.FEEDBACK_THANKS, reply_markup=kb.START)

    @dp.message_handler(content_types=ALLOWED_FEEDBACK_TYPES, reply_to_bot_text=True, admins_chat=True)
    async def admins_reply_message_handler(message: types.Message):
        await communication.admin_message(message)

    @dp.message_handler(reply_to_bot_text=texts.ORDER_CHOOSE_SONG, chat_type=types.ChatType.PRIVATE)
    async def user_search_song_handler(message: types.Message):
        await handlers_.searching.search_audio(message)

    # endregion replies

    # region buttons

    @dp.message_handler(text=kb.MENU.WHAT_PLAYING, chat_type=types.ChatType.PRIVATE)
    async def user_btn_what_playing_handler(message: types.Message):  # Кнопка 'Что играет?'
        await handlers_.users.playlist_now(message)

    @dp.message_handler(text=kb.MENU.ORDER, chat_type=types.ChatType.PRIVATE)
    async def user_btn_order_handler(message: types.Message):  # Кнопка 'Заказать песню'
        await message.answer(texts.ORDER_CHOOSE_SONG, reply_markup=types.ForceReply())
        await message.answer(texts.ORDER_INLINE_SEARCH, reply_markup=kb.ORDER_INLINE)

    @dp.message_handler(text=kb.MENU.FEEDBACK, chat_type=types.ChatType.PRIVATE)
    async def user_btn_feedback_handler(message: types.Message):  # Кнопка 'Обратная связь'
        await message.answer(texts.FEEDBACK, reply_markup=types.ForceReply())

    @dp.message_handler(commands=['help'], chat_type=types.ChatType.PRIVATE)
    @dp.message_handler(text=kb.MENU.HELP, chat_type=types.ChatType.PRIVATE)
    async def user_btn_help_handler(message: types.Message):  # Кнопка 'Помощь'
        await message.answer(texts.HELP['start'], reply_markup=kb.CHOICE_HELP)

    @dp.message_handler(text=kb.MENU.TIMETABLE, chat_type=types.ChatType.PRIVATE)
    async def user_btn_timetable_handler(message: types.Message):  # Кнопка 'Расписание'
        await handlers_.users.timetable(message)

    # endregion buttons

    # region callback
    # region order

    @dp.callback_query_handler(cb=kb.cb.CBOrderDay)  # Выбрали день
    async def query_handler_order_day(query: types.CallbackQuery, cb: kb.cb.CBOrderDay):
        await handlers_.order.order_choose_time(query, cb.day)

    @dp.callback_query_handler(cb=kb.cb.CBOrderTime)  # Выбрали время
    async def query_handler_order_time(query: types.CallbackQuery, cb: kb.cb.CBOrderTime):
        await handlers_.order.order_make(query, Ether(cb.day, cb.time))

    @dp.callback_query_handler(cb=kb.cb.CBOrderBack)  # Кнопка назад при выборе времени
    async def query_handler_order_back(query):
        await handlers_.order.order_choose_day(query)

    @dp.callback_query_handler(cb=kb.cb.CBOrderCancel)  # Кнопка отмены при выборе дня
    async def query_handler_order_cancel(query):
        await handlers_.order.order_cancel(query)

    @dp.callback_query_handler(cb=kb.cb.CBOrderNoTime)  # Выбрал время но туда не влезет
    async def query_handler_order_notime(query: types.CallbackQuery, cb: kb.cb.CBOrderNoTime):
        await handlers_.order.order_no_time(query, cb.day, cb.attempts)

    @dp.callback_query_handler(cb=kb.cb.CBOrderModerate)  # Принять / отклонить
    async def query_handler_order_moderate(query: types.CallbackQuery, cb: kb.cb.CBOrderModerate):
        await handlers_.order.admin_moderate(query, Ether(cb.day, cb.time), kb.STATUS(cb.status))

    @dp.callback_query_handler(cb=kb.cb.CBOrderUnModerate)  # Отменить выбор
    async def query_handler_order_unmoderate(query: types.CallbackQuery, cb: kb.cb.CBOrderUnModerate):
        await handlers_.order.admin_unmoderate(query, Ether(cb.day, cb.time), kb.STATUS(cb.status))

    # endregion order
    # region playlist

    @dp.callback_query_handler(cb=kb.cb.CBPlaylistNext)  # Кнопка "что будет играть" в сообщении "что играет"
    async def query_handler_playlist_next(query):
        await handlers_.users.playlist_next(query)
        await query.answer()

    @dp.callback_query_handler(cb=kb.cb.CBPlaylistDay)  # Выбор дня
    async def query_handler_playlist_day(query: types.CallbackQuery, cb: kb.cb.CBPlaylistDay):
        await handlers_.users.playlist_choose_time(query, cb.day)

    @dp.callback_query_handler(cb=kb.cb.CBPlaylistTime)  # Выбор времени
    async def query_handler_playlist_time(query: types.CallbackQuery, cb: kb.cb.CBPlaylistTime):
        await handlers_.users.playlist_show(query, Ether(cb.day, cb.time))

    @dp.callback_query_handler(cb=kb.cb.CBPlaylistBack)  # Кнопка назад при выборе времени
    async def query_handler_playlist_back(query):
        await handlers_.users.playlist_choose_day(query)

    # @dp.callback_query_handler(cb=kb.cb.CBPlaylistMove)  # Перемещения трека
    # async def query_handler_playlist_move(query: types.CallbackQuery, cb: kb.cb.CBPlaylistMove):
    #     await handlers_.admins.playlist_move(query, cb.index, cb.start_time)

    # endregion playlist
    # region other

    @dp.callback_query_handler(cb=kb.cb.CBOtherHelp)  # Кнопка в сообщении с инструкцией
    async def query_handler_other_help(query: types.CallbackQuery, cb: kb.cb.CBOtherHelp):
        await handlers_.users.help_change(query, cb.key)

    @dp.callback_query_handler()  # Какая то левая кнопка
    async def query_handler_other(query):
        with suppress(exceptions.InvalidQueryID):
            await query.answer("Застара кнопка")

    # endregion other
    # endregion callback

    @dp.message_handler(content_types=['audio'], chat_type=types.ChatType.PRIVATE)
    async def user_audio_handler(message: types.Message):
        return await handlers_.searching.sent_audio(message, message.audio)

    @dp.message_handler(content_types=types.ContentType.ANY, chat_type=types.ChatType.PRIVATE)
    async def user_other_handler(message: types.Message):  # Говорим пользователю что он дурак
        await message.answer_document("BQADAgADlgQAAsedmEuFDrds0XauthYE", texts.UNKNOWN_CMD, reply_markup=kb.START)

    @dp.inline_handler()
    async def inline_query_handler(inline_query: types.InlineQuery):
        await handlers_.searching.inline_search(inline_query)
