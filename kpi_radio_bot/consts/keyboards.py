import json
from datetime import datetime
from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from broadcast import playlist, get_broadcast_num, get_broadcast_name
from consts import _btns_text
from consts._btns_text import MENU, CALLBACKS as CB, STATUS
from consts.others import TIMES_NAME, BROADCAST_TIMES_, HISTORY_CHANNEL_LINK


def _parse(*args) -> str:
    return json.dumps(args)


def unparse(data: str) -> dict:
    return json.loads(data)


def _ikb(text: str, *cb_data) -> InlineKeyboardButton:  # shortcut
    return InlineKeyboardButton(text, callback_data=_parse(*cb_data))

#


ORDER_INLINE = InlineKeyboardMarkup().add(
    InlineKeyboardButton(_btns_text.INLINE_SEARCH, switch_inline_query_current_chat="")
)

START = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton(MENU.WHAT_PLAYING), KeyboardButton(MENU.ORDER)).add(
    KeyboardButton(MENU.FEEDBACK), KeyboardButton(MENU.HELP), KeyboardButton(MENU.TIMETABLE)
)

WHAT_PLAYING = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton(_btns_text.HISTORY, url=HISTORY_CHANNEL_LINK),
    InlineKeyboardButton(_btns_text.NEXT, callback_data=_parse(CB.PLAYLIST, CB.NEXT))
)

CHOICE_HELP = InlineKeyboardMarkup(row_width=1).add(*[
    _ikb(help_value, CB.OTHER, CB.HELP, help_key)
    for help_key, help_value in _btns_text.HELP.items()
])

BAD_ORDER_BUT_OK = InlineKeyboardMarkup(row_width=1).add(
    _ikb(_btns_text.BAD_ORDER_BUT_OK, CB.ORDER, CB.DAY),
    _ikb(_btns_text.CANCEL, CB.ORDER, CB.CANCEL)
)


#


async def order_choose_day() -> InlineKeyboardMarkup:
    day = datetime.today().weekday()
    b_n = get_broadcast_num()
    btns = []

    if b_n is not None and (await playlist.get_broadcast_freetime(day, b_n)) != 0:  # кнопка сейчас если эфир+успевает
        btns.append(_ikb(TIMES_NAME['next_days'][-1], CB.ORDER, CB.TIME, day, b_n))

    if datetime.now().hour < 22:  # кнопка сегодня
        btns.append(_ikb(TIMES_NAME['next_days'][0], CB.ORDER, CB.DAY, day))

    for i in range(1, 4):  # завтра (1), послезавтра (2), послепослезавтра  (3)
        btns.append(_ikb(TIMES_NAME['next_days'][i], CB.ORDER, CB.DAY, (day + i) % 7))

    btns.append(_ikb(_btns_text.CANCEL, CB.ORDER, CB.CANCEL))
    return InlineKeyboardMarkup(row_width=1).add(*btns)


async def order_choose_time(day: int, attempts: int = 5) -> InlineKeyboardMarkup:
    btns = []
    for time, (_, break_finish) in BROADCAST_TIMES_[day].items():
        if day == datetime.today().weekday() and datetime.now().time() > break_finish:
            continue  # если сегодня и перерыв прошел - не добавляем кнопку

        free_minutes = await playlist.get_broadcast_freetime(day, time)

        if free_minutes == 0 and attempts > 0:
            btn = _ikb(get_broadcast_name(time=time), CB.ORDER, CB.NOTIME, day, attempts)
        else:
            btn = _ikb(('⚠' if free_minutes < 5 else '') + get_broadcast_name(time=time), CB.ORDER, CB.TIME, day, time)

        btns.append(btn)

    btns.append(_ikb(_btns_text.BACK, CB.ORDER, CB.BACK))
    return InlineKeyboardMarkup(row_width=2).add(*btns)


#


def admin_choose(day: int, time: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(*[
        _ikb(text, CB.ORDER, CB.MODERATE, day, time, status)
        for status, text in {
            STATUS.QUEUE: _btns_text.QUEUE,
            STATUS.NOW: _btns_text.NOW,
            STATUS.REJECT: _btns_text.REJECT
        }.items()
    ])


def admin_unchoose(day: int, time: int, status: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(_ikb(_btns_text.CANCEL, CB.ORDER, CB.DEMODERATE, day, time, status))


#


def playlist_choose_day() -> InlineKeyboardMarkup:
    today = datetime.today().weekday()
    btns = []
    for day in range(4):
        day = (day + today) % 7
        btns.append(_ikb(get_broadcast_name(day=day), CB.PLAYLIST, CB.DAY, day))
    return InlineKeyboardMarkup(row_width=4).add(*btns)


def playlist_choose_time(day: int) -> InlineKeyboardMarkup:
    btns = [
        _ikb(get_broadcast_name(time=time), CB.PLAYLIST, CB.TIME, day, time)
        for time in BROADCAST_TIMES_[day]
    ]
    btns.append(_ikb(_btns_text.BACK, CB.PLAYLIST, CB.BACK))
    return InlineKeyboardMarkup(row_width=3).add(*btns)


#

_EMOJI_NUMBERS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")


async def playlist_move(playback: List[playlist.PlaylistItem] = None):
    if playback is None:
        playback = await playlist.get_next()
    btns = [
        _ikb(
            f"{_EMOJI_NUMBERS[i]} 🕖{track.time_start.strftime('%H:%M:%S')} {track.title.ljust(120)}.",
            CB.PLAYLIST, CB.MOVE, track.index, track.time_start.timestamp()
        )
        for i, track in enumerate(playback[:10])
    ]
    btns.append(_ikb(f"🔄Обновить", CB.PLAYLIST, CB.MOVE, -1, 0, 0))
    return InlineKeyboardMarkup(row_width=1).add(*btns)
