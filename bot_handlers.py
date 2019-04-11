# Кпи Радио Бот by Владислав Свинки, Ripll 2к!8 - 2к19 t.me/svinerus


from aiogram import Dispatcher, types, executor
from config import *
import db
import bot_utils
import keyboards
import consts
import playlist_api
import music_api
import core

dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_handler(message):
    db.add(message.chat.id)
    if message.chat.id < 0:
        return

    await bot.send_message(message.chat.id, consts.TEXT['start'])
    await bot.send_message(message.chat.id, consts.TEXT['menu'], reply_markup=keyboards.keyboard_start)


@dp.message_handler(commands=['cancel'])
async def cancel(message):
    await bot.send_message(message.chat.id, consts.TEXT['menu'], reply_markup=keyboards.keyboard_start)


@dp.message_handler(lambda m: m.chat.id == ADMINS_CHAT_ID, commands=['next'])
async def next_track_handler(message):
    r = await music_api.radioboss_api(cmd='next')
    await bot.send_message(message.chat.id, 'Ок' if r else 'хуй знает, не работает')


@dp.message_handler(lambda m: m.from_user.id in [185520398, 152950074], commands=['update'])
async def update_handler(message):
    await bot.send_message(message.chat.id, 'Ребутаюсь..')
    bot_utils.reboot()


@dp.message_handler(commands=['ban'])
async def ban_handler(message):
    await core.admin_ban(message)


@dp.callback_query_handler()
async def callback_query_handler(query):
    cmd = query.data.split('-|-')

    # выбрали день
    if cmd[0] == 'predlozka_day':
        await core.predlozka_day(query, int(cmd[1]))

    # выбрали время
    elif cmd[0] == 'predlozka':
        await core.predlozka_time(query, int(cmd[1]), int(cmd[2]))

    # Принять \ подтвердить
    elif cmd[0] == 'predlozka_answ':
        await core.admin_choice(query, cmd[1] == 'ok', int(cmd[2]), int(cmd[3]), int(cmd[4]))

    # Отменить выбор
    elif cmd[0] == 'admin_cancel':
        await core.admin_cancel(query, int(cmd[1]), int(cmd[2]), cmd[3] == 'ok')

    # Проверить текст
    if cmd[0] == 'check_text':
        await core.admin_check_text(query)

    # Кнопка назад при выборе времени
    elif cmd[0] == 'predlozka_back_day':
        await core.predlozka_day_back(query)

    # Кнопка отмены при выборе дня
    elif cmd[0] == 'predlozka_cancel':
        await core.predlozka_cancel(query)

    # Кнопка "предыдущие треки" в сообщении "что играет"
    elif cmd[0] == 'song_prev':
        await core.song_prev(query)

    # Кнопка "следующие треки" в сообщении "что играет"
    elif cmd[0] == 'song_next':
        await core.song_next(query)

    # Кнопка в сообщении с инструкцией
    elif cmd[0] == 'help':
        await core.help_change(query, cmd[1])

    try:
        await bot.answer_callback_query(query.id)
    except:
        pass


@dp.message_handler(content_types=['text', 'audio', 'photo', 'sticker'])
async def message_handler(message):
    # Пользователь скинул аудио
    if message.audio and message.chat.id != ADMINS_CHAT_ID:
        return await bot.send_audio(message.chat.id, message.audio.file_id, 'Теперь выбери день',
                                    reply_markup=keyboards.keyboard_day())

    # Форс реплаи
    if message.reply_to_message and message.reply_to_message.from_user.id == (await bot.me).id:

        # Одменские команды
        if message.chat.id == ADMINS_CHAT_ID:
            # Одмены отвечают
            if message.reply_to_message.audio or message.reply_to_message.forward_from:
                await core.admin_reply(message)

        # Ввод названия песни
        if message.reply_to_message.text == consts.TEXT['predlozka_choose_song']:
            await core.search_audio(message)

        # Обратная связь
        if message.reply_to_message.text == consts.TEXT['feedback']:
            await bot.send_message(message.chat.id, consts.TEXT['feedback_thanks'],
                                   reply_markup=keyboards.keyboard_start)
            await bot.forward_message(ADMINS_CHAT_ID, message.chat.id, message.message_id)

        return

    if message.chat.id < 0:
        return

    # Кнопки

    # Кнопка 'Что играет?'
    if message.text == keyboards.btn['what_playing']:
        playback = await playlist_api.get_now()
        if not playback:
            await bot.send_message(message.chat.id, "Не знаю(", reply_markup=keyboards.keyboard_what_playing)
        else:
            await bot.send_message(message.chat.id, consts.TEXT['what_playing'].format(*playback),
                                   reply_markup=keyboards.keyboard_what_playing)

    # Кнопка 'Предложить песню'
    elif message.text == keyboards.btn['predlozka'] or message.text == '/song':
        await bot.send_message(message.chat.id, consts.TEXT['predlozka_choose_song'],
                               reply_markup=types.ForceReply())
        await bot.send_message(message.chat.id, consts.TEXT['predlozka_inline_search'],
                               reply_markup=keyboards.keyboard_predlozka_inline)

    # Кнопка 'Хочу в команду'
    elif message.text == keyboards.btn['feedback']:
        await bot.send_message(message.chat.id, consts.TEXT['feedback'], reply_markup=types.ForceReply())

    elif message.text == keyboards.btn['help'] or message.text == '/help':
        await bot.send_message(message.chat.id, consts.TEXT['help']['first_msg'],
                               reply_markup=keyboards.keyboard_help)

    else:
        await bot.forward_message(ADMINS_CHAT_ID, message.chat.id, message.message_id)
        await bot.send_message(message.chat.id, consts.TEXT['unknown_cmd'], reply_markup=keyboards.keyboard_start)


@dp.inline_handler()
async def query_text(inline_query):
    await core.inline_search(inline_query)


@dp.edited_message_handler()
async def edited_message(message):
    if message.reply_to_message is None:
        return
    if message.reply_to_message.text == consts.TEXT['predlozka_choose_song']:
        await message_handler(message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
