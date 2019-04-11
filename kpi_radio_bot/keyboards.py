from datetime import datetime
from urllib.parse import quote_plus

from aiogram import types

import consts
from bot_utils import get_break_num, get_break_name
from config import HOST


def _callback(*args):
    return '-|-'.join([str(i) for i in args])


btn = {
    'predlozka': '📝Заказать песню',
    'what_playing': '🎧Что играет?',
    'help': '⁉️Помощь',
    'feedback': '🖌Обратная связь',
}


predlozka_inline = types.InlineKeyboardMarkup()
predlozka_inline.add(types.InlineKeyboardButton("Удобный поиск", switch_inline_query_current_chat=""))

start = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
start.add(types.KeyboardButton(btn['what_playing']), types.KeyboardButton(btn['predlozka']))
start.add(types.KeyboardButton(btn['feedback']), types.KeyboardButton(btn['help']))

what_playing = types.InlineKeyboardMarkup(row_width=2)
what_playing.add(types.InlineKeyboardButton(text='Поиск песни по времени', url='https://t.me/rkpi_music'))
what_playing.add(types.InlineKeyboardButton(text='Предыдущие треки', callback_data='song_prev'),
                 types.InlineKeyboardButton(text='Следующие треки', callback_data='song_next'))

choice_help = types.InlineKeyboardMarkup(row_width=1)
for k, v in consts.help['btns'].items():
    choice_help.add(types.InlineKeyboardButton(text=v, callback_data=_callback('help', k)))


def choice_day() -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btns = []
    day = datetime.today().weekday()

    if get_break_num() is not False:
        btns.append(types.InlineKeyboardButton(
            text=consts.times_name['next_days'][3], callback_data=_callback('predlozka', day, get_break_num())
        ))

    if datetime.now().hour < 22:
        btns.append(types.InlineKeyboardButton(
            text=consts.times_name['next_days'][0], callback_data=_callback('predlozka_day', day)
        ))

    for i in range(1, 3):
        btns.append(types.InlineKeyboardButton(
            text=consts.times_name['next_days'][i], callback_data=_callback('predlozka_day', (day + i) % 7)
        ))

    btns.append(types.InlineKeyboardButton(text='Отмена', callback_data='predlozka_cancel'))
    keyboard.add(*btns)
    return keyboard


def choice_time(day: int) -> types.InlineKeyboardMarkup:

    def get_btn(time: int) -> types.InlineKeyboardButton:
        return types.InlineKeyboardButton(
                text=get_break_name(time),
                callback_data=_callback('predlozka', day, time)
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


def admin(day: int, time: int, audio_name: str, user_id: int) -> types.InlineKeyboardMarkup:
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton(
            text='Принять',
            callback_data=_callback('predlozka_answ', 'ok', user_id, day, time)
        ),
        types.InlineKeyboardButton(
            text='Отклонить',
            callback_data=_callback('predlozka_answ', 'neok', user_id, day, time)
        ),
        types.InlineKeyboardButton(
            text='Посмотреть текст',
            url=f'https://{HOST}/gettext/{quote_plus(audio_name[0:100])}'
        ),
        types.InlineKeyboardButton(
            text='Проверить',
            callback_data='check_text'
        )
    )
    return keyboard
