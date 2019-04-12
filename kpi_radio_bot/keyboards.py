from datetime import datetime

from aiogram import types

import consts
import bot_utils


def _callback(*args):
    return '-|-'.join([str(i) for i in args])


btn = {
    'order': '📝Заказать песню',
    'what_playing': '🎧Что играет?',
    'help': '⁉️Помощь',
    'feedback': '🖌Обратная связь',
}


order_inline = types.InlineKeyboardMarkup()
order_inline.add(types.InlineKeyboardButton("Удобный поиск", switch_inline_query_current_chat=""))

start = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
start.add(types.KeyboardButton(btn['what_playing']), types.KeyboardButton(btn['order']))
start.add(types.KeyboardButton(btn['feedback']), types.KeyboardButton(btn['help']))

what_playing = types.InlineKeyboardMarkup(row_width=2)
what_playing.add(types.InlineKeyboardButton(text='История', url='https://t.me/rkpi_music'))
what_playing.add(types.InlineKeyboardButton(text='Предыдущие треки', callback_data='song_prev'),
                 types.InlineKeyboardButton(text='Следующие треки', callback_data='song_next'))

choice_help = types.InlineKeyboardMarkup(row_width=1)
for k, v in consts.helps['btns'].items():
    choice_help.add(types.InlineKeyboardButton(text=v, callback_data=_callback('help', k)))


async def choice_day() -> types.InlineKeyboardMarkup:
    day = datetime.today().weekday()
    bn = bot_utils.get_break_num()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btns = []

    if bn is not False and (await bot_utils.order_time_left(day, bn)) is not False:  # кнопка сейчас если эфир+успевает
        btns.append(types.InlineKeyboardButton(
            text=consts.times_name['next_days'][3],
            callback_data=_callback('order_time', day, bn)
        ))
    if datetime.now().hour < 22:      # кнопка сегодня
        btns.append(types.InlineKeyboardButton(
            text=consts.times_name['next_days'][0],
            callback_data=_callback('order_day', day)
        ))
    for i in range(1, 3):             # завтра (1), послезавтра (2)
        btns.append(types.InlineKeyboardButton(
            text=consts.times_name['next_days'][i],
            callback_data=_callback('order_day', (day + i) % 7)
        ))
    btns.append(types.InlineKeyboardButton(text='Отмена', callback_data='order_cancel'))
    keyboard.add(*btns)
    return keyboard


async def choice_time(day: int) -> types.InlineKeyboardMarkup:

    async def get_btn(time_: int) -> types.InlineKeyboardButton:
        free_mins = await bot_utils.order_time_left(day, time_)
        if free_mins == 0:
            return types.InlineKeyboardButton(
                text='❌' + bot_utils.get_break_name(time_),
                callback_data=_callback('order_notime')
            )
        return types.InlineKeyboardButton(
                text=('⚠' if free_mins < 5 else '') + bot_utils.get_break_name(time_),
                callback_data=_callback('order_time', day, time_)
            )

    today = day == datetime.today().weekday()
    time = datetime.now().hour * 60 + datetime.now().minute
    times = consts.broadcast_times_['sunday' if day == 6 else 'elseday']

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btns = []

    for num, (_, break_finish) in times.items():
        if today and time > break_finish:  # если сегодня и перерыв прошел - не добавляем кнопку
            continue
        btns.append(await get_btn(num))

    btns.append(types.InlineKeyboardButton(text='Назад', callback_data='order_back_day'))
    keyboard.add(*btns)
    return keyboard


def admin_choose(day: int, time: int) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(
            text='✅Принять',
            callback_data=_callback('admin_choice', day, time, 'queue')
        ),
        types.InlineKeyboardButton(
            text='Без очереди',
            callback_data=_callback('admin_choice', day, time, 'now')
        ),
        types.InlineKeyboardButton(
            text='❌Отклонить',
            callback_data=_callback('admin_choice', day, time, 'reject')
        )
    )


def admin_unchoose(day: int, time: int, status: str) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(
        text='Отмена',
        callback_data=_callback('admin_unchoice', day, time, status)
    ))
