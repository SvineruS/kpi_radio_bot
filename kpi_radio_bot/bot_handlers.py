from aiogram import Dispatcher, types, executor

import consts
import core
import keyboards
from config import *
from utils import other, db, radioboss

dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_handler(message):
    db.add(message.chat.id)
    if message.chat.id < 0:
        return

    await bot.send_message(message.chat.id, consts.TextConstants.START)
    await bot.send_message(message.chat.id, consts.TextConstants.MENU, reply_markup=keyboards.start)


@dp.message_handler(commands=['cancel'])
async def cancel(message):
    await bot.send_message(message.chat.id, consts.TextConstants.MENU, reply_markup=keyboards.start)


@dp.message_handler(lambda m: m.chat.id == ADMINS_CHAT_ID, commands=['next'])
async def next_track_handler(message):
    r = await radioboss.radioboss_api(cmd='next')
    await bot.send_message(message.chat.id, 'Ок' if r else 'хуй знает, не работает')


@dp.message_handler(lambda m: m.from_user.id in [185520398, 152950074], commands=['update'])
async def update_handler(message):
    await bot.send_message(message.chat.id, 'Ребутаюсь..')
    other.reboot()


@dp.message_handler(commands=['ban'])
async def ban_handler(message):
    await core.admins.ban(message)


@dp.message_handler(commands=['vol', 'volume'])
async def volume_handler(message):
    await core.admins.set_volume(message)


@dp.message_handler(commands=['stats'])
async def stats_csv_handler(message):
    await core.admins.get_stats(message)


@dp.message_handler(commands=['notify'])
async def notify_handler(message):
    status = db.notification_get(message.from_user.id)
    db.notification_set(message.from_user.id, not status)
    text = "Уведомления <b>включены</b> \n /notify - выключить" if status else \
        "Уведомления <b>выключены</b> \n /notify - включить"
    await bot.send_message(message.chat.id, text)


@dp.callback_query_handler()
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
        await bot.edit_message_reply_markup(query.message.chat.id, query.message.message_id,
                                            reply_markup=await keyboards.choice_time(int(cmd[1]), int(cmd[2]) - 1))
        await bot.answer_callback_query(query.id, consts.TextConstants.ORDER_ERR_TOOLATE)

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

    #
    # Кнопка в сообщении с инструкцией
    elif cmd[0] == 'help':
        await core.users.help_change(query, cmd[1])

    try:
        await bot.answer_callback_query(query.id)
    except:
        pass


@dp.message_handler(content_types=['text', 'audio', 'photo', 'sticker'])
async def message_handler(message):
    # Пользователь скинул аудио
    if message.audio and message.chat.id != ADMINS_CHAT_ID:
        return await bot.send_audio(message.chat.id, message.audio.file_id, consts.TextConstants.ORDER_CHOOSE_DAY,
                                    reply_markup=await keyboards.choice_day())

    # Форс реплаи
    if message.reply_to_message and message.reply_to_message.from_user.id == (await bot.me).id:

        # Одменские команды
        if message.chat.id == ADMINS_CHAT_ID:
            # Одмены отвечают
            if message.reply_to_message.audio or message.reply_to_message.forward_date:  # not None if sender hidden
                await core.communication.admin_message(message)

            return

        # Ввод названия песни
        if message.reply_to_message.text == consts.TextConstants.ORDER_CHOOSE_SONG:
            return await core.search.search_audio(message)

        # Реплай на сообщение обратной связи или сообщение от модера
        # if message.reply_to_message.text == consts.TextConstants.FEEDBACK or \
        #        core.communication.cache_is_set(message.reply_to_message.message_id):
        await core.communication.user_message(message)
        return await bot.send_message(message.chat.id, consts.TextConstants.FEEDBACK_THANKS,
                                          reply_markup=keyboards.start)

        

    if message.chat.id < 0:
        return

    # Кнопки

    # Кнопка 'Что играет?'
    if message.text == consts.BtnConstants.MENU['what_playing']:
        return await core.users.song_now(message)

    # Кнопка 'Предложить песню'
    if message.text == consts.BtnConstants.MENU['order'] or message.text == '/song':
        await bot.send_message(message.chat.id, consts.TextConstants.ORDER_CHOOSE_SONG, reply_markup=types.ForceReply())
        return await bot.send_message(message.chat.id, consts.TextConstants.ORDER_INLINE_SEARCH,
                                      reply_markup=keyboards.order_inline)

    # Кнопка 'Обратная связь'
    if message.text == consts.BtnConstants.MENU['feedback']:
        return await bot.send_message(message.chat.id, consts.TextConstants.FEEDBACK, reply_markup=types.ForceReply())

    # Кнопка 'Помощь'
    if message.text == consts.BtnConstants.MENU['help'] or message.text == '/help':
        return await bot.send_message(message.chat.id, consts.TextConstants.HELP['start'],
                                      reply_markup=keyboards.choice_help)

    # Кнопка 'Расписание'
    if message.text == consts.BtnConstants.MENU['timetable']:
        return await core.users.timetable(message)

    # Просто сообщение
    await bot.send_document(message.chat.id, "BQADAgADlgQAAsedmEuFDrds0XauthYE",
                            caption=consts.TextConstants.UNKNOWN_CMD, reply_markup=keyboards.start)
    await core.communication.user_message(message)


@dp.inline_handler()
async def query_text(inline_query):
    await core.search.inline_search(inline_query)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
