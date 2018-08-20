# -*- coding: utf-8 -*-

import os
import requests
from telebot import types
from datetime import datetime


CONFIG = {
    'start': '''Привет, это бот РадиоКПИ. 
Ты можешь заказать песню, задать любой вопрос, также мы открыты для предложений.
Узнать что сейчас играет
Узнать как стать частью ламповой команды РадиоКПИ.
Узнать, что происходит на РадиоКПИ прямо сейчас.''',
    'menu': 'Выбери, что хочешь сделать 😜',

    'feedback': 'Ты можешь оставить отзыв о работе РадиоКПИ или вступить в наши ряды! \n \
Напиши сообщение и админы ответят тебе! \n(⛔️/cancel)',
    'feedback_thanks': 'Спасибо за заявку, мы обязательно рассмотрим ее!',

    'predlozka_choose_song': 'Что ты хочешь услышать? (Исполнитель - песня) \n(⛔️/cancel)',
    'predlozka_moderating': 'Спасибо за заказ ({0}), ожидайте модерации!',  # время
    'predlozka_ok': 'Ваш заказ ({0}) принят!',  # название песни
    'predlozka_ok_next': 'Ваш заказ ({0}) принят и заиграет прямо сейчас!',
    'predlozka_neok': 'Ваш заказ ({0}) отклонен(',

    'what_played_choose_time': 'Напиши примерное время когда играла песня (например 18:20) \n(⛔️/cancel)',

    'error': 'Не получилось(',

    'save_pic': 'Окей, кидай фотошки, я залью!',

    'pics_path': 'D:\\pics\\',
    'days1': ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'],
    'days2': ['Сегодня', 'Завтра', 'Послезавтра', 'Сейчас'],
    'times': ['Первый', 'Второй', 'Третий', 'Четвертый'],
}

btn = {
    'what_playing': '🎧Что сейчас играет?',
    'predlozka': '📝Заказать песню',
    'feedback_v_komandu': '🖌Обратная связь',
    'pokazhi': '📷Покажи радио',
}


def get_music_path(day, time):
    t = 'D:\\Вещание Радио\\'
    # В воскресенье только дневной(0) и вечерний(1) эфир
    if day == 6:
        t += '({0}){1}\\{2}\\'.format(day+1, CONFIG['days1'][day], ['Дневной эфир', 'Вечерний эфир'][time-1])
    # До вечернего эфира
    elif time < 5:
        t += 'Перерыв\\0{0}_{1}\\{2}.{3} перерыв\\'.format(
            day+1, CONFIG['days1'][day], time, CONFIG['times'][time-1])
    # Вечерний эфир
    else:
        t += '({0}){1}\\'.format(day+1, CONFIG['days1'][day])

    return t


def keyboard_start():
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    keyboard.add(*[types.KeyboardButton(btn[t]) for t in btn])
    return keyboard


def keyboard_day():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btns = []
    day = datetime.today().weekday()

    if get_break_num() != 0:
        btns.append(types.InlineKeyboardButton(
            text=CONFIG['days2'][3], callback_data='predlozka-|-' + str(day) + '-|-' + str(get_break_num())))

    if datetime.now().hour < 22:
        btns.append(types.InlineKeyboardButton(
            text=CONFIG['days2'][0], callback_data='predlozka_day-|-' + str(day)))

    for i in range(1, 3):
        btns.append(types.InlineKeyboardButton(
            text=CONFIG['days2'][i], callback_data='predlozka_day-|-' + str((day+i) % 7)))

    btns.append(types.InlineKeyboardButton(text='Отмена', callback_data='predlozka_cancel'))
    keyboard.add(*btns)
    return keyboard


def keyboard_time(day):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    time = datetime.now().hour * 60 + datetime.now().minute
    today = day == datetime.today().weekday()

    if day == 6:
        if not today or time < 18 * 60:
            btns.append(types.InlineKeyboardButton(text='Днем', callback_data='predlozka-|-6-|-1'))
        btns.append(types.InlineKeyboardButton(text='Вечером', callback_data='predlozka-|-6-|-2'))
    else:
        for i in range(1, 5):
            if today and time > 8*60+30 + 115*i:
                continue  # после конца перерыва убираем кнопку
            btns.append(types.InlineKeyboardButton(
                text='После ' + str(i) + ' пары',
                callback_data='predlozka-|-' + str(day) + '-|-' + str(i)
            ))

        btns.append(types.InlineKeyboardButton(
                text='Вечером', callback_data='predlozka-|-' + str(day) + '-|-' + '5'))

    btns.append(types.InlineKeyboardButton(text='Назад', callback_data='predlozka_back_day'))
    keyboard.add(*btns)
    return keyboard


def get_audio_name(audio):
    name = str(audio.performer) + ' - ' + str(audio.title)
    name = ''.join(list(filter(lambda c: (c not in '\/:*?"<>|'), name)))  # винда агрится на эти символы в пути
    return name


def get_user_name(user_obj):
    return '<a href="tg://user?id={0}">{1}</a>'.format(user_obj.id, user_obj.first_name)


def save_file(url, to):
    dirname = os.path.dirname(to)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    if os.path.isfile(to):
        return

    print('Donwloading... ', to)
    try:
        file = requests.get(url, stream=True)
        f = open(to, 'wb')
        for chunk in file.iter_content(chunk_size=512):
            if chunk:
                f.write(chunk)
        f.close()
        print('downloaded')
    except Exception as e:
        print('Error: download!', e)


def get_break_num(time=None):
    day = datetime.today().weekday()
    if not time:
        time = datetime.now()
    time = time.hour * 60 + time.minute

    if time > 22*60 or time < 10*60+5:
        return 0

    # Воскресенье
    if day == 6:
        if 11*60+15 < time < 18*60:
            return 1
        if time > 18*60:
            return 2

    # Вечерний эфир
    if time > 17*60+50:
        return 5

    # Перерыв
    for i in range(4):
        # 10:05 + пара * i (10:05 - начало 1 перерыва)
        if 0 < time - (10*60+5 + i*115) < 18:  # сдвиг на 2 минуты для удобства
            return i+1

    #Пара
    return 0


def check_bad_words(text):
    if 'Ошибка' in text:
        return text

    bad_words = ['пизд',
                 'бля',
                 'хуй', 'хуя', 'хуи', 'хуе',
                 'ебать', 'еби', 'ебло', 'ебля', 'ебуч',
                 'долбо',
                 'дрочит',
                 'мудак', 'мудило',
                 'пидор', 'пидар',
                 'сука', 'суку',
                 'гандон',
                 'fuck']

    answ = []
    for word in bad_words:
        if word in text:
            answ.append(word)

    if not answ:
        return "Все ок вродь"
    else:
        return "Нашел это: " + ' '.join(answ)
