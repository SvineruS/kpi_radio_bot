# -*- coding: utf-8 -*-

# Хочу оставить большой комментарий типа я крутой программист.
# Модуль бота кпи радио by Владислав Свинкин 2к!8 t.me/svinerus
# Новый модуль bot_utils.py - с константами, текстами и кучкой функций
# Все, что не нужно выкладывать в гитхаб в config.py
# Токен и чат админов там!!!!


import telebot

import music_api
import bot_utils
import db
import ban
import playlist_api
from config import *

from datetime import datetime
from os import listdir, system, getcwd
from random import choice


if __name__ == '__main__':
    TOKEN = TOKEN_TEST
    ADMINS_CHAT_ID = 185520398

bot = telebot.TeleBot(TOKEN)

bot_me = bot.get_me()
print('Запускаем ботика..', bot_me)
bot.send_message(185520398, 'Я включилсо')


@bot.message_handler(commands=['start'])
def start_handler(message):
    db.add(message.chat.id)
    if message.chat.id < 0:
        return

    t = message.text.split(' ')
    if len(t) == 2:
        bot.send_message(message.chat.id, 'Ищем нужную песню...')
        bot.send_chat_action(message.chat.id, 'upload_audio')
        if '/' in t[1]:
            bot.send_audio(message.chat.id, 'http://'+WEB_DOMAIN+'/download/'+t[1])
        else:
            bot.send_audio(message.chat.id, 'http://'+WEB_DOMAIN+'/playlist/prev/play/'+t[1])

        return

    bot.send_message(message.chat.id, bot_utils.CONFIG['start'])
    bot.send_message(message.chat.id, bot_utils.CONFIG['menu'], reply_markup=bot_utils.keyboard_start())


@bot.message_handler(commands=['help'])
def help_handler(message):
    bot.send_message(message.chat.id, bot_utils.CONFIG['help'], parse_mode='HTML')


@bot.message_handler(commands=['cancel'])
def moar(message):
    bot.send_message(message.chat.id, bot_utils.CONFIG['menu'], reply_markup=bot_utils.keyboard_start())


@bot.message_handler(commands=['save_pic'])
def save_pic_request(message):
    if message.chat.id == ADMINS_CHAT_ID:
        bot.send_message(message.chat.id, bot_utils.CONFIG['save_pic'], reply_markup=telebot.types.ForceReply())


@bot.message_handler(commands=['update'])
def update_handler(message):
    if message.from_user.id != 185520398:
        return
    bot.send_message(message.chat.id, 'Ребутаюсь..')
    system(r'cmd.exe /C start '+getcwd() + '\\update.bat')


@bot.message_handler(commands=['ban'])
def ban_handler(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return
    if message.reply_to_message is None:
        bot.send_message(message.chat.id, "Перешлите сообщение пользователя, которого нужно забанить")
        return

    cmd = message.text.split(' ')
    user = message.reply_to_message.caption_entities[0].user if message.reply_to_message.audio else message.reply_to_message.forward_from
    ban_time = int(cmd[1]) if len(cmd) >= 2 else 60 * 24
    reason = " Причина: " + ' '.join(cmd[2:]) if len(cmd) >= 3 else ""
    ban_time = str(ban.ban_user(user.id, ban_time))

    if ban_time == "0":
        bot.send_message(message.chat.id, "Пользователь " + bot_utils.get_user_name(user) + " разбанен", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "Пользователь " + bot_utils.get_user_name(user)
                         + " забанен на " + ban_time + " минут." + reason, parse_mode="HTML")
        bot.send_message(user.id, "Вы были забанены на " + ban_time + " минут." + reason, parse_mode="HTML")


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
    # Если админы выбрали отмену:
    #
    #   cmd[3] = ok\neok
    #   cmd[4] = msg_id
    #

    elif cmd[0] == 'predlozka' or cmd[0] == 'admin_cancel':
        if cmd[0] == 'admin_cancel':
            user_obj = query.message.caption_entities[0].user
            user_id = user_obj.id
        else:
            user_id = query.message.chat.id
            user_obj = query.from_user

        text = bot_utils.CONFIG['days1'][int(cmd[1])] + ', '
        if cmd[2] == '-1':
            text += 'днем'
        elif cmd[2] == '5':
            text += 'вечером'
        else:
            text += 'после ' + cmd[2] + ' пары'

        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(*[
            telebot.types.InlineKeyboardButton(
                text='Принять',
                callback_data='-|-'.join(['predlozka_answ', 'ok', str(user_id), cmd[1], cmd[2]])),
            telebot.types.InlineKeyboardButton(
                text='Отклонить',
                callback_data='-|-'.join(['predlozka_answ', 'neok', str(user_id), cmd[1], cmd[2]])),
            telebot.types.InlineKeyboardButton(
                text='Посмотреть текст',
                url=('http://'+WEB_DOMAIN+'/gettext/' + bot_utils.get_audio_name(query.message.audio))[0:100]),  # trim
            telebot.types.InlineKeyboardButton(
                text='Проверить',
                callback_data='-|-'.join(['predlozka_answ', 'check']))
        ])

        now = int(cmd[1]) == datetime.today().weekday() and int(cmd[2]) == bot_utils.get_break_num()
        admin_text = ('‼️' if now else '❗️') + 'Новый заказ - ' + text + (' (сейчас!)' if now else '') + \
                                               ' от ' + bot_utils.get_user_name(user_obj)

        if cmd[0] == 'predlozka':

            is_ban = ban.chek_ban(user_id)
            if is_ban:
                bot.send_message(query.message.chat.id, "Вы не можете предлагать музыку до " +
                                 datetime.fromtimestamp(is_ban).strftime("%d.%m %H:%M"))
                return

            bot.edit_message_caption(caption=bot_utils.CONFIG['predlozka_moderating'].format(text),
                                     chat_id=query.message.chat.id, message_id=query.message.message_id,
                                     reply_markup=telebot.types.InlineKeyboardMarkup())

            bot.send_message(user_id, bot_utils.CONFIG['menu'], reply_markup=bot_utils.keyboard_start())

            bot.send_audio(ADMINS_CHAT_ID, query.message.audio.file_id, admin_text,
                           reply_markup=keyboard, parse_mode='HTML')

        elif cmd[0] == 'admin_cancel':
            bot.edit_message_caption(caption=admin_text, chat_id=ADMINS_CHAT_ID, message_id=query.message.message_id,
                                     reply_markup=keyboard, parse_mode='HTML')
            if cmd[3] == 'ok':
                path = str(bot_utils.get_music_path(int(cmd[1]), int(cmd[2])) /
                           (bot_utils.get_audio_name(query.message.audio) + '.mp3'))

                for i in music_api.radioboss_api(action='getplaylist2'):  # удалить из плейлиста радиобосса
                    if i.attrib['FILENAME'] == path:
                        music_api.radioboss_api(action='delete', pos=i.attrib['INDEX'])
                        break
                bot_utils.delete_file(path)  # удалить с диска




    # Админы выбрали принять\отменить
    #
    #   cmd[1] = ok или neok
    #   cmd[2] = айди заказавшего
    #   cmd[3] = выбранный день
    #   cmd[4] = выбранное время
    #
    elif cmd[0] == 'predlozka_answ':
        name = bot_utils.get_audio_name(query.message.audio)

        if cmd[1] == 'check':
            text = music_api.search_text(name)
            n = bot_utils.check_bad_words(text)
            bot.answer_callback_query(query.id, text=n)
            return

        new_text = 'Заказ: ' + query.message.caption.split(' - ')[1].split(' от')[0] + \
                   ', от ' + bot_utils.get_user_name(query.message.caption_entities[0].user) + \
                   ' - ' + ("✅Принят" if cmd[1] == 'ok' else "❌Отклонен") + \
                   ' (' + bot_utils.get_user_name(query.from_user) + ')'

        keyboard_cancel = telebot.types.InlineKeyboardMarkup()
        keyboard_cancel.add(telebot.types.InlineKeyboardButton(
            text='Отмена',
            callback_data='-|-'.join(['admin_cancel', cmd[3], cmd[4], cmd[1]])))

        bot.edit_message_caption(caption=new_text,
                                 chat_id=query.message.chat.id, message_id=query.message.message_id,
                                 reply_markup=keyboard_cancel, parse_mode='HTML')

        url = 'https://api.telegram.org/file/bot{0}/{1}'.format(
            TOKEN, bot.get_file(query.message.audio.file_id).file_path)

        if cmd[1] == 'ok':
            to = bot_utils.get_music_path(int(cmd[3]), int(cmd[4])) / (name + '.mp3')

            bot_utils.save_file(url, to)
            bot_utils.write_sender_tag(to, query.message.caption_entities[0].user)

            if int(cmd[3]) == datetime.today().weekday() and int(cmd[4]) == bot_utils.get_break_num():
                music_api.radioboss_api(action='inserttrack', filename=to, pos=-2)
                bot.send_message(int(cmd[2]), bot_utils.CONFIG['predlozka_ok_next'].format(name))
            else:
                bot.send_message(int(cmd[2]), bot_utils.CONFIG['predlozka_ok'].format(name))
        elif cmd[1] == 'neok':
            bot.send_message(int(cmd[2]), bot_utils.CONFIG['predlozka_neok'].format(name))


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
    elif cmd[0] == 'song_prev':
        playback = playlist_api.prev_get()
        if not playback:
            bot.send_message(query.message.chat.id, 'Не знаю(', reply_markup=bot_utils.keyboard_start())
        else:
            text = ''
            for track in playback:
                text += '🕖<b>{0}</b> {1}\n'.format(track['time_start'], track['title'])
                #  bot.answer_callback_query(callback_query_id=query.id, text=text, show_alert=True)  # мб так красивее, хз
            bot.send_message(query.message.chat.id, text, parse_mode='HTML')

    # Кнопка "следующие треки" в сообщении "что играет" #
    elif cmd[0] == 'song_next':
        playback = playlist_api.next_get()
        if not playback:
            bot.send_message(query.message.chat.id, 'Доступно только во время эфира', reply_markup=bot_utils.keyboard_start())
        else:
            text = ''
            for track in playback:
                text += '🕖<b>{0}</b> {1}\n'.format(track['time_start'], track['title'])
            bot.send_message(query.message.chat.id, text, parse_mode='HTML')

    bot.answer_callback_query(query.id)


@bot.message_handler(content_types=['text', 'audio', 'photo', 'sticker'])
def message_handler(message):
    # Пользователь скинул аудио
    if message.audio and message.chat.id != ADMINS_CHAT_ID:
        msg = bot.send_audio(message.chat.id, message.audio.file_id, 'Теперь выбери день',
                             reply_markup=bot_utils.keyboard_day())
        bot_utils.auto_check_bad_words(msg, bot)
        return

    # Форс реплаи
    if message.reply_to_message and message.reply_to_message.from_user.id == bot_me.id:

        # Одменские команды
        if message.chat.id == ADMINS_CHAT_ID:
            # Одмены отвечают
            if message.reply_to_message.audio or message.reply_to_message.forward_from:
                if message.reply_to_message.audio:  # на заказ
                    to = message.reply_to_message.caption_entities[0].user.id
                    txt = "На ваш заказ _" + bot_utils.get_audio_name(message.reply_to_message.audio) + "_ ответили:"

                if message.reply_to_message.forward_from:  # на отзыв
                    to = message.reply_to_message.forward_from.id
                    txt = "  На ваше сообщение ответили: "

                bot.send_message(to, txt)
                if message.audio:
                    bot.send_audio(to, message.audio.file_id)
                elif message.sticker:
                    bot.send_sticker(to, message.sticker.file_id)
                elif message.photo:
                    bot.send_photo(to, message.photo.file_id)
                else:
                    bot.send_message(to, message.text)



            # Сохранение картинок
            if message.reply_to_message.text == bot_utils.CONFIG['save_pic']:
                url = 'https://api.telegram.org/file/bot{0}/{1}'.format(
                    TOKEN, bot.get_file(message.photo[0].file_id).file_path)
                bot_utils.save_file(url, bot_utils.CONFIG['pics_path'] + str(message.photo[0].file_size) + '.jpg')

        # Ввод названия песни
        if message.reply_to_message.text == bot_utils.CONFIG['predlozka_choose_song']:
            bot.send_chat_action(message.chat.id, 'upload_audio')
            audio = music_api.search(message.text)

            if not audio:
                bot.send_message(message.chat.id,
                                 'Ничего не нашел( \nМожешь загрузить свое аудио сам или переслать от другого бота!',
                                 reply_markup=bot_utils.keyboard_start())
            else:
                audio = audio[0]
                try:
                    audio_file = music_api.download(audio['url'])  # неочевидная хуйня: скачивание файла шоб поставить норм имя песне
                    msg = bot.send_audio(message.chat.id, audio_file,
                                         'Выбери день (или отредактируй название)',
                                         performer=audio['artist'], title=audio['title'],
                                         reply_markup=bot_utils.keyboard_day())
                    bot_utils.auto_check_bad_words(msg, bot)
                except Exception as e:
                    print('Error: loading audio!', e)
                    bot.send_message(message.chat.id, bot_utils.CONFIG['error'],
                                     reply_markup=bot_utils.keyboard_start())

        # Обратная связь
        if message.reply_to_message.text == bot_utils.CONFIG['feedback']:
            bot.send_message(message.chat.id, bot_utils.CONFIG['feedback_thanks'], reply_markup=bot_utils.keyboard_start())
            bot.forward_message(ADMINS_CHAT_ID, message.chat.id, message.message_id)

        return

    if message.chat.id < 0:
        return


    # Кнопки

    # Кнопка 'Что играет?'
    if message.text == bot_utils.btn['what_playing']:
        keyboard = telebot.types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(telebot.types.InlineKeyboardButton(text='Поиск песни по времени', url='http://r.kpi.ua/history'))
        keyboard.add(telebot.types.InlineKeyboardButton(text='Предыдущие треки', callback_data='song_prev'),
                     telebot.types.InlineKeyboardButton(text='Следующие треки', callback_data='song_next'))

        playback = playlist_api.now_get()
        if not playback:
            bot.send_message(message.chat.id, "Не знаю(", reply_markup=keyboard)
        else:
            bot.send_message(message.chat.id, bot_utils.CONFIG['what_playing'].format(*playback),
                             parse_mode='HTML', reply_markup=keyboard)


    # Кнопка 'Предложить песню'
    elif message.text == bot_utils.btn['predlozka'] or \
         message.text == '/song':

        bot.send_message(message.chat.id, bot_utils.CONFIG['predlozka_choose_song'],
                         reply_markup=telebot.types.ForceReply(), parse_mode="HTML")
        bot.send_message(message.chat.id, bot_utils.CONFIG['predlozka_inline_search'],
                         reply_markup=bot_utils.keyboard_predlozka_inline, parse_mode="HTML")

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
        bot.forward_message(ADMINS_CHAT_ID, message.chat.id, message.message_id)
        bot.send_message(message.chat.id, 'Шо ты хош? Для заказа песни не забывай нажимать на кнопку "Заказать песню". Помощь тут /help', reply_markup=bot_utils.keyboard_start())


@bot.inline_handler(func=lambda kek: True)
def query_text(inline_query):
    name = inline_query.query
    music = music_api.search(name)
    if not music:
        bot.answer_inline_query(inline_query.id, [])
        return
    articles = []
    for i in range(min(50, len(music))):
        audio = music[i]
        if not audio or not audio['url']:
            continue
        articles.append(
            telebot.types.InlineQueryResultAudio(
                i, audio['url'],
                performer=audio['artist'],
                title=audio['title']
            )
        )
    if articles:
        bot.answer_inline_query(inline_query.id, articles)


@bot.edited_message_handler(func=lambda message: True)
def edited_message(message):
    if message.reply_to_message is None:
        return
    if message.reply_to_message.text == bot_utils.CONFIG['predlozka_choose_song']:
        message_handler(message)


def send_history(fields):
    if not fields['artist'] and not fields['title']:
        fields['title'] = fields['casttitle']

    sender_name = bot_utils.read_sender_tag(fields['path'])
    if not sender_name:
        sender_name = 'От команды РадиоКпи'
    else:
        sender_name = 'Заказал ' + sender_name

    print(sender_name)

    #f = open(fields['path'], 'rb')
    #m = f.read()
    #f.close()

    #bot.send_audio(HISTORY_CHAT_ID, m, performer=fields['artist'], title=fields['title'],
    #               caption=sender_name, parse_mode='HTML')


if __name__ == '__main__':
    bot.remove_webhook()
    bot.polling(none_stop=True)
