# -*- coding: utf-8 -*-
import logging
import os
import xml.etree.ElementTree as Etree
from aiogram import types
from datetime import datetime
from urllib.parse import quote
from music_api import radioboss_api
from base64 import b64decode, b64encode
from config import *
from typing import Union


TEXT = {
    'start': '''Привет, это бот РадиоКПИ. 
Ты можешь:
 - Заказать песню   
 - Задать любой вопрос
 - Узнать что играет сейчас, играло или будет играть
 - Узнать как стать частью ламповой команды РадиоКПИ.
 - Узнать, что происходит на РадиоКПИ прямо сейчас.
 
⁉️Советуем прочитать инструкцию /help
''',
    'menu': 'Выбери, что хочешь сделать 😜',

    'help': '''
📝Есть 3 способа <b>заказать песню:</b>
- Нажать на кнопку <code>Заказать песню</code> и ввести название, бот выберет наиболее вероятный вариант
- Использовать инлайн режим поиска (ввести <code>@kpiradio_bot</code> или нажать на соответствующую кнопку). 
    В этом случае ты можешь выбрать из 10 найденных вариантов, с возможностью сначала послушать
- Загрузить или переслать боту желаемую песню

После этого необходимо выбрать день и время для заказа.

<b>❗️Советы:</b>
- Не отправляйте слишком много песен сразу, их все еще принимают люди, а не нейросети
- Учтите, что у песен с нехорошими словами или смыслом высокий шанс не пройти модерацию
- Приветствуются песни на украинском <i>(гугл "квоты на радио")</i>
- Приветствуются нейтральные, спокойные песни, которые не будут отвлекать от учебного процесса 

<b>🖌Обратная связь:</b>
- Вы всегда можете написать команде админов что вы думаете о них и о радио
- Если хотите стать частью радио - пишите об этом и готовьтесь к анкетам
- Считаете что то неудобным? Есть предложения по улучшению? Не задумываясь пиши нам.

<b>⏭Плейлист радио:</b>
- Узнать что играет сейчас, играло до этого или будет играть можно нажав на кнопку "<code>Что играет</code>"
- Помните дату и время когда играла песня и хотите ее найти? Можете найти ее там же -> <code>Поиск песни по времени</code>
- Если вы заказываете песню во время эфира, мы постараемся сделать так, что бы она заиграла следующей

Можешь посетить наш сайт! http://r.kpi.ua
''',

    'feedback': 'Ты можешь оставить отзыв о работе РадиоКПИ или предложить свою кандидатуру для вступления в наши ряды! \n \
Напиши сообщение и админы ответят тебе! \n(⛔️/cancel)',
    'feedback_thanks': 'Спасибо за заявку, мы обязательно рассмотрим ее!',

    'predlozka_choose_song': 'Что ты хочешь услышать? Напиши название или скинь свою песню\n(⛔️/cancel)',
    'predlozka_inline_search': 'Нажми на кнопку для более удобного поиска 👀',

    'predlozka_moderating': 'Спасибо за заказ ({0}), ожидайте модерации!',  # время
    'predlozka_ok': 'Ваш заказ ({0}) принят!',  # название песни
    'predlozka_ok_next': 'Ваш заказ ({0}) принят и заиграет прямо сейчас!',
    'predlozka_neok': 'Ваш заказ ({0}) отклонен(',

    'what_playing': """⏮ <b>Предыдущий трек: </b> {0}, 
▶️ <b>Сейчас играет: </b> {1}
⏭ <b>Следующий трек: </b> {2}""",

    'error': 'Не получилось(',
    'unknown_cmd': 'Шо ты хош? Для заказа песни не забывай нажимать на кнопку "Заказать песню". Помощь тут /help',

    'song_no_prev': 'Не знаю(',
    'song_no_next': 'Доступно только во время эфира',
    

    'days1': ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'],
    'days2': ['Сегодня', 'Завтра', 'Послезавтра', 'Сейчас'],
    'times': ['Утрений эфир', 'Первый перерыв', 'Второй перерыв', 'Третий перерыв', 'Четвертый перерыв', 'Вечерний эфир'],
}

btn = {
    'predlozka': '📝Заказать песню',
    'what_playing': '🎧Что играет?',
    'feedback_v_komandu': '🖌Обратная связь',
}

keyboard_predlozka_inline = types.InlineKeyboardMarkup()
keyboard_predlozka_inline.add(types.InlineKeyboardButton("Удобный поиск", switch_inline_query_current_chat=""))

keyboard_start = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
keyboard_start.add(types.KeyboardButton(btn['predlozka']))
keyboard_start.add(types.KeyboardButton(btn['what_playing']), types.KeyboardButton(btn['feedback_v_komandu']))

keyboard_what_playing = types.InlineKeyboardMarkup(row_width=2)
keyboard_what_playing.add(types.InlineKeyboardButton(text='Поиск песни по времени', url='https://t.me/rkpi_music'))
keyboard_what_playing.add(types.InlineKeyboardButton(text='Предыдущие треки', callback_data='song_prev'),
                          types.InlineKeyboardButton(text='Следующие треки', callback_data='song_next'))


def get_music_path(day: int, time: int = None, archive: bool = None) -> Path:
    t = Path('D:/Вещание Радио/')
    t /= 'Эфир' if archive else 'Заказы'
    t /= '0{0}_{1}'.format(day + 1, TEXT['days1'][day])

    if time is False:  # сука 0 считается как False
        return t

    if day == 6:  # В воскресенье только утренний(0) и вечерний эфир(5)
        t /= TEXT['times'][time]
    elif time < 5:  # До вечернего эфира
        t /= '{0}.{1}'.format(time, TEXT['times'][time])
    else:  # Вечерний эфир
        t /= '({0}){1}\\'.format(day + 1, TEXT['days1'][day])

    return t


def get_break_num(time: datetime = None) -> Union[False, int]:
    if not time:
        time = datetime.now()
        day = datetime.today().weekday()
    else:
        day = time.weekday()
    time = time.hour * 60 + time.minute

    if time > 22 * 60 or time < 7 * 60:
        return False

    if day == 6:  # Воскресенье
        if 11 * 60 + 15 < time < 18 * 60:  # Утренний эфир
            return 0
        if time > 18 * 60:  # Вечерний эфир
            return 5

    if time <= 8 * 60 + 30:  # Утренний эфир
        return 0

    if time >= 17 * 60 + 50:  # Вечерний эфир
        return 5

    for i in range(4):  # Перерыв
        # 10:05 + пара * i   (10:05 - начало 1 перерыва)
        if 0 <= time - (10 * 60 + 5 + i * 115) <= 20:
            return i + 1

    # Не перерыв
    return False


def get_break_name(time: int) -> str:
    return TEXT['times'][time]


def is_break_now(day: int, time: int) -> bool:
    return day == datetime.today().weekday() and time == get_break_num()


def keyboard_day() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btns = []
    day = datetime.today().weekday()

    if get_break_num() is not False:
        btns.append(types.InlineKeyboardButton(
            text=TEXT['days2'][3], callback_data='predlozka-|-' + str(day) + '-|-' + str(get_break_num())))

    if datetime.now().hour < 22:
        btns.append(types.InlineKeyboardButton(
            text=TEXT['days2'][0], callback_data='predlozka_day-|-' + str(day)))

    for i in range(1, 3):
        btns.append(types.InlineKeyboardButton(
            text=TEXT['days2'][i], callback_data='predlozka_day-|-' + str((day + i) % 7)))

    btns.append(types.InlineKeyboardButton(text='Отмена', callback_data='predlozka_cancel'))
    keyboard.add(*btns)
    return keyboard


def keyboard_time(day: int) -> types.InlineKeyboardMarkup:

    def get_btn(time: int) -> types.InlineKeyboardButton:
        return types.InlineKeyboardButton(
                text=get_break_name(time),
                callback_data=f'predlozka-|-{day}-|-{time}'
            )

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    time = datetime.now().hour * 60 + datetime.now().minute
    today = day == datetime.today().weekday()

    if day == 6:
        if not today or time < 18 * 60:
            btns.append(get_btn(0))
    else:
        for i in range(0, 5):
            if today and time > 8 * 60 + 30 + 115 * i:
                continue  # после конца перерыва убираем кнопку
            btns.append(get_btn(i))

    btns.append(get_btn(5))

    btns.append(types.InlineKeyboardButton(text='Назад', callback_data='predlozka_back_day'))
    keyboard.add(*btns)
    return keyboard


def keyboard_admin(day: int, time: int, audio_name: str, user_id: int) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            text='Принять',
            callback_data='-|-'.join(['predlozka_answ', 'ok', str(user_id), str(day), str(time)])
        ),
        types.InlineKeyboardButton(
            text='Отклонить',
            callback_data='-|-'.join(['predlozka_answ', 'neok', str(user_id), str(day), str(time)])
        ),
        types.InlineKeyboardButton(
            text='Посмотреть текст',
            url=f'https://{HOST}/gettext/{quote(audio_name[0:100])}'
        ),
        types.InlineKeyboardButton(
            text='Проверить',
            callback_data='check_text'
        )
    )
    return keyboard


def get_audio_name(audio: types.Audio) -> str:
    if not audio.performer and not audio.title:
        name = 'Названия нету :('
    else:
        name = ' - '.join([str(audio.performer), str(audio.title)])
    name = ''.join(list(filter(lambda c: (c not in '/:*?"<>|'), name)))  # винда агрится на эти символы в пути
    return name


def get_user_name(user_obj: types.User) -> str:
    return '<a href="tg://user?id={0}">{1}</a>'.format(user_obj.id, user_obj.first_name)


def create_dirs(to: Union[str, Path]) -> None:
    dirname = os.path.dirname(to)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    if os.path.isfile(to):
        return


def delete_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        path.unlink()
    except Exception as ex:
        logging.error(f'delete file: {ex} {path}')


async def write_sender_tag(path: Path, user_obj: types.User) -> None:
    tags = await radioboss_api(action='readtag', fn=path)
    name = get_user_name(user_obj)
    name = b64encode(name.encode('utf-8')).decode('utf-8')
    tags[0].attrib['Comment'] = name
    xmlstr = Etree.tostring(tags, encoding='utf8', method='xml').decode('utf-8')
    await radioboss_api(action='writetag', fn=path, data=xmlstr)


async def read_sender_tag(path: Path) -> Union[False, str]:
    tags = await radioboss_api(action='readtag', fn=path)
    name = tags[0].attrib['Comment']
    try:
        name = b64decode(name).decode('utf-8')
    except:
        return False
    return name


def check_bad_words(text: str) -> str:
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


def reboot() -> None:
    os.system(r'cmd.exe /C start ' + os.getcwd() + '\\update.bat')

