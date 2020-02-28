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
    types.InlineKeyboardButton(text=_btns_text.HISTORY, url='https://t.me/rkpi_music'),
    types.InlineKeyboardButton(text=_btns_text.NEXT, callback_data='song_next')
)

CHOICE_HELP = types.InlineKeyboardMarkup(row_width=1).add(*[
    types.InlineKeyboardButton(text=v, callback_data=_callback('help', k))
    for k, v in _btns_text.HELP.items()
])

BAD_ORDER_BUT_OK = types.InlineKeyboardMarkup(row_width=1).add(
    types.InlineKeyboardButton(text=_btns_text.BAD_ORDER_BUT_OK, callback_data=_callback('bad_order_but_ok')),
    types.InlineKeyboardButton(text=_btns_text.CANCEL, callback_data='order_cancel')
)


async def choice_day() -> types.InlineKeyboardMarkup:
    day = datetime.today().weekday()
    b_n = get_broadcast_num()
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    btns = []

    if b_n is not False and (await playlist.get_broadcast_freetime(day, b_n)) != 0:  # кнопка сейчас если эфир+успевает
        btns.append(types.InlineKeyboardButton(
            text=TIMES_NAME['next_days'][-1],
            callback_data=_callback('order_time', day, b_n)
        ))
    if datetime.now().hour < 22:  # кнопка сегодня
        btns.append(types.InlineKeyboardButton(
            text=TIMES_NAME['next_days'][0],
            callback_data=_callback('order_day', day)
        ))
    for i in range(1, 4):  # завтра (1), послезавтра (2), послепослезавтра  (3)
        btns.append(types.InlineKeyboardButton(
            text=TIMES_NAME['next_days'][i],
            callback_data=_callback('order_day', (day + i) % 7)
        ))
    btns.append(types.InlineKeyboardButton(text=_btns_text.CANCEL, callback_data='order_cancel'))
    keyboard.add(*btns)
    return keyboard


async def choice_time(day: int, attempts: int = 5) -> types.InlineKeyboardMarkup:
    async def get_btn(time_: int) -> types.InlineKeyboardButton:
        free_mins = await playlist.get_broadcast_freetime(day, time_)
        if free_mins == 0 and attempts > 0:
            return types.InlineKeyboardButton(
                text='❌' + get_broadcast_name(time_),
                callback_data=_callback('order_notime', day, attempts)
            )
        return types.InlineKeyboardButton(
            text=('⚠' if free_mins < 5 else '') + get_broadcast_name(time_),
            callback_data=_callback('order_time', day, time_)
        )

    today = day == datetime.today().weekday()
    time = datetime.now().hour * 60 + datetime.now().minute
    times = BROADCAST_TIMES_[day]

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    btns = []

    for num, (_, break_finish) in times.items():
        if today and time > break_finish:  # если сегодня и перерыв прошел - не добавляем кнопку
            continue
        btns.append(await get_btn(num))

    btns.append(types.InlineKeyboardButton(text=_btns_text.BACK, callback_data='order_back_day'))
    keyboard.add(*btns)
    return keyboard


def admin_choose(day: int, time: int) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton(
            text=_btns_text.QUEUE,
            callback_data=_callback('admin_choice', day, time, 'queue')
        ),
        types.InlineKeyboardButton(
            text=_btns_text.NOW,
            callback_data=_callback('admin_choice', day, time, 'now')
        ),
        types.InlineKeyboardButton(
            text=_btns_text.REJECT,
            callback_data=_callback('admin_choice', day, time, 'reject')
        )
    )


def admin_unchoose(day: int, time: int, status: str) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(
        text=_btns_text.CANCEL,
        callback_data=_callback('admin_unchoice', day, time, status)
    ))
