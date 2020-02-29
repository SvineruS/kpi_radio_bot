from datetime import datetime

from aiogram import types

from broadcast import playlist, get_broadcast_num, get_broadcast_name
from consts import _btns_text
from consts.others import TIMES_NAME, BROADCAST_TIMES_


def _callback(*args):
    return '-|-'.join([str(i) for i in args])


MAIN_MENU = _btns_text.MENU

ORDER_INLINE = types.InlineKeyboardMarkup().add(
    types.InlineKeyboardButton(_btns_text.INLINE_SEARCH, switch_inline_query_current_chat="")
)

START = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton(_btns_text.MENU['what_playing']), types.KeyboardButton(_btns_text.MENU['order'])
).add(
    types.KeyboardButton(_btns_text.MENU['feedback']), types.KeyboardButton(_btns_text.MENU['help']),
    types.KeyboardButton(_btns_text.MENU['timetable'])
)

WHAT_PLAYING = types.InlineKeyboardMarkup(row_width=2).add(
    types.InlineKeyboardButton(_btns_text.HISTORY, url='https://t.me/rkpi_music'),
    types.InlineKeyboardButton(_btns_text.NEXT, callback_data='playlist_next')
)

CHOICE_HELP = types.InlineKeyboardMarkup(row_width=1).add(*[
    types.InlineKeyboardButton(v, callback_data=_callback('help', k))
    for k, v in _btns_text.HELP.items()
])

BAD_ORDER_BUT_OK = types.InlineKeyboardMarkup(row_width=1).add(
    types.InlineKeyboardButton(_btns_text.BAD_ORDER_BUT_OK, callback_data=_callback('bad_order_but_ok')),
    types.InlineKeyboardButton(_btns_text.CANCEL, callback_data='order_cancel')
)


#


async def order_choose_day() -> types.InlineKeyboardMarkup:
    day = datetime.today().weekday()
    b_n = get_broadcast_num()
    btns = []

    if b_n is not False and (await playlist.get_broadcast_freetime(day, b_n)) != 0:  # кнопка сейчас если эфир+успевает
        btns.append(types.InlineKeyboardButton(
            TIMES_NAME['next_days'][-1], callback_data=_callback('order_time', day, b_n)
        ))
    if datetime.now().hour < 22:  # кнопка сегодня
        btns.append(types.InlineKeyboardButton(
            TIMES_NAME['next_days'][0], callback_data=_callback('order_day', day)
        ))
    for i in range(1, 4):  # завтра (1), послезавтра (2), послепослезавтра  (3)
        btns.append(types.InlineKeyboardButton(
            TIMES_NAME['next_days'][i], callback_data=_callback('order_day', (day + i) % 7)
        ))

    btns.append(types.InlineKeyboardButton(_btns_text.CANCEL, callback_data='order_cancel'))
    return types.InlineKeyboardMarkup(row_width=1).add(*btns)


async def order_choose_time(day: int, attempts: int = 5) -> types.InlineKeyboardMarkup:
    async def get_btn(time_: int) -> types.InlineKeyboardButton:
        free_mins = await playlist.get_broadcast_freetime(day, time_)

        if free_mins == 0 and attempts > 0:
            return types.InlineKeyboardButton(
                get_broadcast_name(time_), callback_data=_callback('order_notime', day, attempts)
            )
        return types.InlineKeyboardButton(
            ('⚠' if free_mins < 5 else '') + get_broadcast_name(time_),
            callback_data=_callback('order_time', day, time_)
        )

    btns = []
    for num, (_, break_finish) in BROADCAST_TIMES_[day].items():
        if day == datetime.today().weekday() and datetime.now().time() > break_finish:
            continue  # если сегодня и перерыв прошел - не добавляем кнопку
        btns.append(await get_btn(num))

    btns.append(types.InlineKeyboardButton(_btns_text.BACK, callback_data='order_back_day'))
    return types.InlineKeyboardMarkup(row_width=2).add(*btns)


#


def admin_choose(day: int, time: int) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup().add(*[
        types.InlineKeyboardButton(text, callback_data=_callback('admin_choice', day, time, status))
        for status, text in (('queue', _btns_text.QUEUE), ('now', _btns_text.NOW), ('reject', _btns_text.REJECT))
    ])


def admin_unchoose(day: int, time: int, status: str) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(
        _btns_text.CANCEL, callback_data=_callback('admin_unchoice', day, time, status)
    ))


#


def playlist_choose_day() -> types.InlineKeyboardMarkup:
    today = datetime.today().weekday()
    btns = []
    for day in range(4):
        day = (day + today) % 7
        btns.append(types.InlineKeyboardButton(
            TIMES_NAME['week_days'][day], callback_data=_callback('playlist_day', day)
        ))
    return types.InlineKeyboardMarkup(row_width=4).add(*btns)


def playlist_choose_time(day: int) -> types.InlineKeyboardMarkup:
    btns = [
        types.InlineKeyboardButton(get_broadcast_name(time), callback_data=_callback('playlist_time', day, time))
        for time in BROADCAST_TIMES_[day]
    ]
    btns.append(types.InlineKeyboardButton(_btns_text.BACK, callback_data='playlist_back'))
    return types.InlineKeyboardMarkup(row_width=3).add(*btns)
