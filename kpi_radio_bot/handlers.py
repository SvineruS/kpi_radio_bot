""" Хендлеры бота """

import logging

from aiogram import Dispatcher, types, executor

import core
from config import BOT, ADMINS_CHAT_ID
from consts import keyboards, texts
from utils import bot_filters

DP = Dispatcher(BOT)
bot_filters.bind_filters(DP)


@DP.message_handler(commands=['start'])
async def start_handler(message):
    if message.chat.id < 0:
        return

    await core.users.add_in_db(message)
    await BOT.send_message(message.chat.id, texts.START)
    await core.users.menu(message)


@DP.message_handler(commands=['cancel'])
async def cancel(message):
    await core.users.menu(message)


@DP.message_handler(commands=['notify'])
async def notify_handler(message):
    await core.users.notify_switch(message)


# region admins

@DP.message_handler(commands=['next'], admins_chat=True)
async def next_handler(message):
    await core.admins.next_track(message)


@DP.message_handler(commands=['update'], admins_chat=True)
async def update_handler(message):
    await core.admins.update(message)


@DP.message_handler(commands=['ban'], admins_chat=True)
async def ban_handler(message):
    await core.admins.ban(message)


@DP.message_handler(commands=['vol', 'volume'], admins_chat=True)
async def volume_handler(message):
    await core.admins.set_volume(message)


@DP.message_handler(commands=['stats'], admins_chat=True)
async def stats_handler(message):
    await core.admins.get_stats(message)


@DP.message_handler(commands=['log'], admins_chat=True)
async def log_handler(message):
    await core.admins.get_log(message)


# endregion


@DP.callback_query_handler()
async def callback_query_handler(query):
    cmd = query.data.split('-|-')

    #
    # Выбрали день
    if cmd[0] == 'order_day':
        await core.order.order_day_choiced(query, int(cmd[1]))

    # Выбрали время
    elif cmd[0] == 'order_time':
        await core.order.order_time_choiced(query, int(cmd[1]), int(cmd[2]))

    # Кнопка назад при выборе времени
    elif cmd[0] == 'order_back_day':
        await core.order.order_day_unchoiced(query)

    # Кнопка отмены при выборе дня
    elif cmd[0] == 'order_cancel':
        await core.order.order_cancel(query)

    # Выбрал время но туда не влезет
    elif cmd[0] == 'order_notime':
        await BOT.edit_message_reply_markup(query.message.chat.id, query.message.message_id,
                                            reply_markup=await keyboards.choice_time(int(cmd[1]), int(cmd[2]) - 1))
        await BOT.answer_callback_query(query.id, texts.ORDER_ERR_TOOLATE)

    #
    # Принять / отклонить
    elif cmd[0] == 'admin_choice':
        await core.order.admin_choice(query, int(cmd[1]), int(cmd[2]), cmd[3])

    # Отменить выбор
    elif cmd[0] == 'admin_unchoice':
        await core.order.admin_unchoice(query, int(cmd[1]), int(cmd[2]), cmd[3])

    #
    # Кнопка "следующие треки" в сообщении "что играет"
    elif cmd[0] == 'song_next':
        await core.users.song_next(query)

    # Кнопка в сообщении с инструкцией
    elif cmd[0] == 'help':
        await core.users.help_change(query, cmd[1])

    # Кнопка "все ок" когда закинул неподобающий трек
    elif cmd[0] == 'bad_order_but_ok':
        await BOT.edit_message_caption(
            query.message.chat.id, query.message.message_id,
            caption=texts.ORDER_CHOOSE_DAY, reply_markup=await keyboards.choice_day())

    try:
        await BOT.answer_callback_query(query.id)
    except Exception as ex:
        logging.warning(f"pls add exception {ex} in except")


@DP.message_handler(content_types=['text', 'audio', 'photo', 'sticker'])
async def message_handler(message):
    # Форс реплаи
    if message.reply_to_message and message.reply_to_message.from_user.id == (await BOT.me).id:

        # Одменские команды
        if message.chat.id == ADMINS_CHAT_ID:
            # Одмены отвечают
            return await core.communication.admin_message(message)

        # Ввод названия песни
        if message.reply_to_message.text == texts.ORDER_CHOOSE_SONG and not message.audio:
            return await core.search.search_audio(message)

        # Реплай на сообщение обратной связи или сообщение от модера
        if message.reply_to_message.text == texts.FEEDBACK or \
                core.communication.cache_is_set(message.reply_to_message.message_id):
            await core.communication.user_message(message)
            return await BOT.send_message(message.chat.id, texts.FEEDBACK_THANKS,
                                          reply_markup=keyboards.START)

        # Реплай, но на какую то хуйню
        if not message.audio:
            return await BOT.send_message(message.chat.id, texts.FEEDBACK_PLS_USE_BUTTON)

    if message.chat.id < 0:
        return

    # Пользователь скинул аудио
    if message.audio:
        return await core.users.send_audio(message.chat.id, tg_audio=message.audio)

    # Кнопки

    # Кнопка 'Что играет?'
    if message.text == keyboards.MAIN_MENU['what_playing']:
        return await core.users.song_now(message)

    # Кнопка 'Предложить песню'
    if message.text == keyboards.MAIN_MENU['order'] or message.text == '/song':
        await BOT.send_message(message.chat.id, texts.ORDER_CHOOSE_SONG, reply_markup=types.ForceReply())
        return await BOT.send_message(message.chat.id, texts.ORDER_INLINE_SEARCH,
                                      reply_markup=keyboards.ORDER_INLINE)

    # Кнопка 'Обратная связь'
    if message.text == keyboards.MAIN_MENU['feedback']:
        return await BOT.send_message(message.chat.id, texts.FEEDBACK, reply_markup=types.ForceReply())

    # Кнопка 'Помощь'
    if message.text == keyboards.MAIN_MENU['help'] or message.text == '/help':
        return await BOT.send_message(message.chat.id, texts.HELP['start'],
                                      reply_markup=keyboards.CHOICE_HELP)

    # Кнопка 'Расписание'
    if message.text == keyboards.MAIN_MENU['timetable']:
        return await core.users.timetable(message)

    # Просто сообщение
    await BOT.send_document(message.chat.id, "BQADAgADlgQAAsedmEuFDrds0XauthYE",
                            caption=texts.UNKNOWN_CMD, reply_markup=keyboards.START)


@DP.inline_handler()
async def query_text(inline_query):
    await core.search.inline_search(inline_query)


if __name__ == '__main__':
    executor.start_polling(DP, skip_updates=True)
