# -*- coding: utf-8 -*-

# Хочу оставить большой комментарий типа я крутой программист.
# Модуль бота кпи радио by Владислав Свинкин 2к!8 t.me/svinerus
# Новый модуль bot_utils.py - с константами, текстами и кучкой функций
# Все, что не нужно выкладывать в гитхаб в passwords.py
# Токен и чат админов там!!!!


import telebot
import requests

from db import db
from datetime import datetime
from time import strptime, strftime
from os import listdir
from random import choice
from sys import exit as sys_exit
from subprocess import Popen, CREATE_NEW_CONSOLE

import bot_utils
from passwords import *

if __name__ == '__main__':
    bot = telebot.TeleBot(TOKEN_TEST)
    ADMINS_CHAT_ID = 185520398
else:
    bot = telebot.TeleBot(TOKEN)

bot_me = bot.get_me()
print('Запускаем ботика..', bot_me)


@bot.message_handler(commands=['start', 'help', 'song'])
def start(message):
    if db.find_one({'usr': message.chat.id}) is None:
        db.insert({'usr': message.chat.id})
    if message.chat.id < 0:
        return

    bot.send_message(message.chat.id, bot_utils.CONFIG['start'])
    bot.send_message(message.chat.id, bot_utils.CONFIG['menu'], reply_markup=bot_utils.keyboard_start())


@bot.message_handler(commands=['cancel'])
def moar(message):
    bot.send_message(message.chat.id, bot_utils.CONFIG['menu'], reply_markup=bot_utils.keyboard_start())


@bot.message_handler(commands=['save_pic'])
def save_pic_request(message):
    if message.chat.id == ADMINS_CHAT_ID:
        bot.send_message(message.chat.id, bot_utils.CONFIG['save_pic'], reply_markup=telebot.types.ForceReply())


@bot.message_handler(commands=['update'])
def update(message):
    if message.chat.id != 185520398:
        return
#    Popen(r'update.bat', creationflags=CREATE_NEW_CONSOLE)




@bot.callback_query_handler(func=lambda c: True)
def callback_query_handler(query):
    cmd = query.data.split('-|-')

    # Выбрал день, отправляю клавиатуру выбора времени
    #
    #   cmd[1] = выбранный день
    #
    if cmd[0] == 'predlozka_day':
        bot.edit_message_caption(
            chat_id=query.message.chat.id, message_id=query.message.message_id,
            caption=bot_utils.CONFIG['days1'][int(cmd[1])] + ', отлично. Теперь выбери время',
            reply_markup=bot_utils.keyboard_time(int(cmd[1]))
        )

    # Выбрал время, отправляю это все админам
    #
    #   cmd[1] = выбранный день
    #   cmd[2] = выбранное время
    #
    elif cmd[0] == 'predlozka':
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(telebot.types.InlineKeyboardButton(
            text='Принять',
            callback_data='-|-'.join(['predlozka_answ', 'ok', str(query.message.chat.id), cmd[1], cmd[2]])))
        keyboard.add(telebot.types.InlineKeyboardButton(
            text='Отклонить',
            callback_data='-|-'.join(['predlozka_answ', 'neok', str(query.message.chat.id)])))

        t = bot_utils.CONFIG['days1'][int(cmd[1])] + ', '
        if cmd[1] == '6':  # в воскресенье есть только дневной (0) и вечерний (1) эфир
            t += 'днем' if cmd[2] == 0 else 'вечером'
        else:
            t += 'вечером' if cmd[2] == '5' else 'после ' + cmd[2] + ' пары'
        if int(cmd[1]) == datetime.today().weekday() and int(cmd[2]) == bot_utils.get_break_num():
            t += ' (cейчас!)'

        bot.send_audio(ADMINS_CHAT_ID, query.message.audio.file_id,
                       'Новый заказ, ' + t + bot_utils.get_user_name(query.from_user),
                       reply_markup=keyboard, parse_mode='HTML')
        bot.edit_message_caption(caption=bot_utils.CONFIG['predlozka_moderating'].format(t),
                                 chat_id=query.message.chat.id, message_id=query.message.message_id,
                                 reply_markup=telebot.types.InlineKeyboardMarkup())
        bot.send_message(query.message.chat.id, bot_utils.CONFIG['menu'], reply_markup=bot_utils.keyboard_start())

    # Админы выбрали принять\отменить
    #
    #   cmd[1] = ok или neok
    #   cmd[2] = айди заказавшего
    #   cmd[3] = выбранный день
    #   cmd[4] = выбранное время
    #
    elif cmd[0] == 'predlozka_answ':
        name = str(query.message.audio.performer) + ' - ' + str(query.message.audio.title)
        bot.edit_message_caption(caption=query.message.caption +' - '+cmd[1]+'('+bot_utils.get_user_name(query.from_user)+')',
                                 chat_id=query.message.chat.id, message_id=query.message.message_id,
                                 reply_markup=telebot.types.InlineKeyboardMarkup(), parse_mode='HTML')
        if cmd[1] == 'ok':
            url = 'https://api.telegram.org/file/bot{0}/{1}'.format(
                    TOKEN, bot.get_file(query.message.audio.file_id).file_path)
            to = bot_utils.get_music_path(int(cmd[3]), int(cmd[4])) + name + '.mp3'

            bot_utils.save_file(url, to)
            if int(cmd[3]) == datetime.today().weekday() and int(cmd[4]) == bot_utils.get_break_num():
                bot_utils.radioboss_api(action='inserttrack', filename=to, pos=-2)
                t = bot_utils.CONFIG['predlozka_ok_next'].format(name)
            else:
                t = bot_utils.CONFIG['predlozka_ok'].format(name)
        else:
            t = bot_utils.CONFIG['predlozka_neok'].format(name)

        bot.send_message(int(cmd[2]), t)

    #
    # Кнопка назад при выборе времени
    elif cmd[0] == 'predlozka_back_day':
        bot.edit_message_caption(
            chat_id=query.message.chat.id, message_id=query.message.message_id,
            caption='Выбери день', reply_markup=bot_utils.keyboard_day()
        )
    # Кнопка отмены при выборе дня
    elif cmd[0] == 'predlozka_cancel':
        bot.edit_message_caption(
            chat_id=query.message.chat.id, message_id=query.message.message_id,
            caption='Ну ок(', reply_markup=telebot.types.InlineKeyboardMarkup()
        )
        bot.send_message(query.message.chat.id, bot_utils.CONFIG['menu'], reply_markup=bot_utils.keyboard_start())

    # Кнопка "предыдущие треки" в сообщении "что играет"
    elif cmd[0] == 'song_played':
        playback = bot_utils.radioboss_api(action='getlastplayed')
        if playback:
            text = ''
            try:
                for i in range(min(5, len(playback))):
                    track = playback[i].attrib
                    text += '🕖{0}: {1}\n'.format(track['STARTTIME'].split(' ')[1], track['CASTTITLE'])
#  bot.answer_callback_query(callback_query_id=query.id, text=text, show_alert=True)  # мб так красивее, хз
                bot.send_message(query.message.chat.id, text)
            except:
                pass
        bot.send_message(query.message.chat.id, bot_utils.CONFIG['menu'], reply_markup=bot_utils.keyboard_start())

    # Кнопка ввода вермени в сообщении "что играет"
    if cmd[0] == 'song_played_time':
        bot.send_message(query.message.chat.id, bot_utils.CONFIG['what_played_choose_time'],
                         reply_markup=telebot.types.ForceReply())

    bot.answer_callback_query(callback_query_id=query.id)


@bot.message_handler(content_types=['text', 'photo'])
def message_handler(message):
    # Форс реплаи
    if message.reply_to_message and message.reply_to_message.from_user.id == bot_me.id:

        # Одменские команды
        if message.chat.id == ADMINS_CHAT_ID:

            # Одмены отвечают на отзыв
            if message.reply_to_message.forward_from:
                bot.send_message(message.reply_to_message.forward_from.id, "На ваше сообщение ответили\n"+message.text)

            # Сохранение картинок
            if message.reply_to_message.text == bot_utils.CONFIG['save_pic']:
                url = 'https://api.telegram.org/file/bot{0}/{1}'.format(
                    TOKEN, bot.get_file(message.photo[0].file_id).file_path)
                bot_utils.save_file(url, bot_utils.CONFIG['pics_path'] + str(message.photo[0].file_size) + '.jpg')

        # Ввод названия песни
        if message.reply_to_message.text == bot_utils.CONFIG['predlozka_choose_song']:
            bot.send_chat_action(message.chat.id, 'upload_audio')
            audio = bot_utils.find_song(message.text)

            if not audio:
                bot.send_message(message.chat.id, 'Ничего не нашел( \nНо ты можешь загрузить свое аудио сам!',
                                 reply_markup=bot_utils.keyboard_start())
            else:
                try:
                    audio_file = requests.get(audio['download'], stream=True).raw
                    bot.send_audio(message.chat.id, audio_file, ' (или отредактируй название)',
                                   performer=audio['artist'], title=audio['title'],
                                   reply_markup=bot_utils.keyboard_day())

                except Exception as e:
                    print('Error: loading audio!', e)
                    bot.send_message(message.chat.id, bot_utils.CONFIG['error'],
                                     reply_markup=bot_utils.keyboard_start())

        # Заявка на вступление в команду
        if message.reply_to_message.text == bot_utils.CONFIG['feedback']:
            bot.send_message(message.chat.id, bot_utils.CONFIG['feedback_thanks'], reply_markup=bot_utils.keyboard_start())
            bot.forward_message(ADMINS_CHAT_ID, message.chat.id, message.message_id)

        # Выбор времени для поиска песни по времени
        if message.reply_to_message.text == bot_utils.CONFIG['what_played_choose_time']:
            try:
                dt = strptime(message.text, '%H:%M')
                user_time = dt.tm_hour*60+dt.tm_min
            except:
                bot.send_message(message.chat.id, "Похоже, что вы неправильно написали время :)")
            
            playback = bot_utils.radioboss_api(action='getlastplayed')
            if playback:
                text = ''
                old_day = 0
                try:
                    for i in range(min(100, len(playback))):
                        track = playback[i].attrib
                        dt = strptime(track['STARTTIME'], '%Y-%m-%d %H:%M:%S')
                        time = dt.tm_hour * 60 + dt.tm_min
                        
                        if abs(time - user_time) < 10:
                            if dt.tm_mday != old_day:
                                text += "\n📅{0}".format(strftime("%d.%m", dt))
                                old_day = dt.tm_mday
                            text += "\n🕓{0}: {1}".format(strftime("%H:%M", dt), track['CASTTITLE'])
                    if text:
                        bot.send_message(message.chat.id, text)
                    else:
                        bot.send_message(message.chat.id, 'Видимо, в это время ничего не играло')
                except Exception as e:
                    print(e)
        return

    if message.chat.id < 0:
        return

    # Кнопки

    # Кнопка 'Что играет?'
    if message.text == bot_utils.btn['what_playing']:
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*[telebot.types.InlineKeyboardButton(text='Предыдущие треки', callback_data='song_played'),
                telebot.types.InlineKeyboardButton(text='Поиск песни по времени', callback_data='song_played_time')])

        playback = bot_utils.radioboss_api(action='playbackinfo')
        if playback:
            try:
                if playback[3].attrib['state'] == 'stop':
                    bot.send_message(message.chat.id, "Ничего", reply_markup=keyboard)
                else:
                    bot.send_message(message.chat.id,
                                     '⏮ *Предыдущий трек: *' + playback[0][0].attrib['CASTTITLE'] +
                                     '\n▶️ *Сейчас играет: *' + playback[1][0].attrib['CASTTITLE'] +
                                     '\n⏭ *Следующий трек: *' + playback[2][0].attrib['CASTTITLE'],
                                     parse_mode='Markdown', reply_markup=keyboard)
            except Exception as e:
                print('Error! what playing', e)
                bot.send_message(message.chat.id, 'Ничего', reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, 'Не знаю(')

    # Кнопка 'Предложить песню'
    elif message.text == bot_utils.btn['predlozka']:
        bot.send_message(message.chat.id, bot_utils.CONFIG['predlozka_choose_song'],
                         reply_markup=telebot.types.ForceReply())

    # Кнопка 'Хочу в команду'
    elif message.text == bot_utils.btn['feedback_v_komandu']:
        bot.send_message(message.chat.id, bot_utils.CONFIG['feedback'], reply_markup=telebot.types.ForceReply())

    # Кнопка 'Покажи радио'
    elif message.text == bot_utils.btn['pokazhi']:
        try:
            pics = listdir(bot_utils.CONFIG['pics_path'])
            pic = open(bot_utils.CONFIG['pics_path'] + choice(pics), 'rb')
            bot.send_photo(message.chat.id, pic)
        except Exception as e:
            print('Error: send pic!', e)
            bot.send_message(message.chat.id, bot_utils.CONFIG['error'])

    else:
        bot.send_message(message.chat.id, 'Шо ты хош?', reply_markup=bot_utils.keyboard_start())


@bot.message_handler(content_types=['audio'])
def message_width_audio(message):
    bot.send_audio(message.chat.id, message.audio.file_id, 'Теперь выбери день', reply_markup=bot_utils.keyboard_day())


@bot.edited_message_handler(func=lambda message: True)
def edited_message(message):
    if message.reply_to_message is None:
        return
    if message.reply_to_message.text == bot_utils.CONFIG['predlozka_choose_song'] or \
       message.reply_to_message.text == bot_utils.CONFIG['what_played_choose_time']:
        message_handler(message)


if __name__ == '__main__':
    bot.polling(none_stop=True)
