import json
from datetime import datetime
from typing import List

from aiogram import types

from broadcast import playlist, get_broadcast_num, get_broadcast_name
from consts import _btns_text
from consts._btns_text import MENU, CALLBACKS as CB, STATUS
from consts.others import TIMES_NAME, BROADCAST_TIMES_, HISTORY_CHANNEL_LINK


def _parse(*args) -> str:
    return json.dumps(args)


def unparse(data: str) -> dict:
    return json.loads(data)


#


ORDER_INLINE = types.InlineKeyboardMarkup().add(
    types.InlineKeyboardButton(_btns_text.INLINE_SEARCH, switch_inline_query_current_chat="")
)

START = types.ReplyKeyboardMarkup(resize_keyboard=True).add(
    types.KeyboardButton(MENU.WHAT_PLAYING), types.KeyboardButton(MENU.ORDER)
).add(
    types.KeyboardButton(MENU.FEEDBACK), types.KeyboardButton(MENU.HELP),
    types.KeyboardButton(MENU.TIMETABLE)
)

WHAT_PLAYING = types.InlineKeyboardMarkup(row_width=2).add(
    types.InlineKeyboardButton(_btns_text.HISTORY, url=HISTORY_CHANNEL_LINK),
    types.InlineKeyboardButton(_btns_text.NEXT, callback_data=_parse(CB.PLAYLIST, CB.NEXT))
)

CHOICE_HELP = types.InlineKeyboardMarkup(row_width=1).add(*[
    types.InlineKeyboardButton(v, callback_data=_parse(CB.OTHER, CB.HELP, k))
    for k, v in _btns_text.HELP.items()
])

BAD_ORDER_BUT_OK = types.InlineKeyboardMarkup(row_width=1).add(
    types.InlineKeyboardButton(_btns_text.BAD_ORDER_BUT_OK, callback_data=_parse(CB.ORDER, CB.DAY)),
    types.InlineKeyboardButton(_btns_text.CANCEL, callback_data=_parse(CB.ORDER, CB.CANCEL))
)


#


async def order_choose_day() -> types.InlineKeyboardMarkup:
    day = datetime.today().weekday()
    b_n = get_broadcast_num()
    btns = []

    if b_n is not None and (await playlist.get_broadcast_freetime(day, b_n)) != 0:  # кнопка сейчас если эфир+успевает
        btns.append(types.InlineKeyboardButton(
            TIMES_NAME['next_days'][-1], callback_data=_parse(CB.ORDER, CB.TIME, day, b_n)
        ))
    if datetime.now().hour < 22:  # кнопка сегодня
        btns.append(types.InlineKeyboardButton(
            TIMES_NAME['next_days'][0], callback_data=_parse(CB.ORDER, CB.DAY, day)
        ))
    for i in range(1, 4):  # завтра (1), послезавтра (2), послепослезавтра  (3)
        btns.append(types.InlineKeyboardButton(
            TIMES_NAME['next_days'][i], callback_data=_parse(CB.ORDER, CB.DAY, (day + i) % 7)
        ))

    btns.append(types.InlineKeyboardButton(_btns_text.CANCEL, callback_data=_parse(CB.ORDER, CB.CANCEL)))
    return types.InlineKeyboardMarkup(row_width=1).add(*btns)


async def order_choose_time(day: int, attempts: int = 5) -> types.InlineKeyboardMarkup:
    btns = []
    for time, (_, break_finish) in BROADCAST_TIMES_[day].items():
        if day == datetime.today().weekday() and datetime.now().time() > break_finish:
            continue  # если сегодня и перерыв прошел - не добавляем кнопку

        free_minutes = await playlist.get_broadcast_freetime(day, time)

        if free_minutes == 0 and attempts > 0:
            btn = types.InlineKeyboardButton(get_broadcast_name(time=time),
                                             callback_data=_parse(CB.ORDER, CB.NOTIME, day, attempts))
        else:
            btn = types.InlineKeyboardButton(('⚠' if free_minutes < 5 else '') + get_broadcast_name(time=time),
                                             callback_data=_parse(CB.ORDER, CB.TIME, day, time))

        btns.append(btn)

    btns.append(types.InlineKeyboardButton(_btns_text.BACK, callback_data=_parse(CB.ORDER, CB.BACK)))
    return types.InlineKeyboardMarkup(row_width=2).add(*btns)


#


def admin_choose(day: int, time: int) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup().add(*[
        types.InlineKeyboardButton(text, callback_data=_parse(CB.ORDER, CB.MODERATE, day, time, status))
        for status, text in {
            STATUS.QUEUE: _btns_text.QUEUE,
            STATUS.NOW: _btns_text.NOW,
            STATUS.REJECT: _btns_text.REJECT
        }.items()
    ])


def admin_unchoose(day: int, time: int, status: str) -> types.InlineKeyboardMarkup:
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(
        _btns_text.CANCEL, callback_data=_parse(CB.ORDER, CB.DEMODERATE, day, time, status)
    ))


#


def playlist_choose_day() -> types.InlineKeyboardMarkup:
    today = datetime.today().weekday()
    btns = []
    for day in range(4):
        day = (day + today) % 7
        btns.append(types.InlineKeyboardButton(
            get_broadcast_name(day=day), callback_data=_parse(CB.PLAYLIST, CB.DAY, day)
        ))
    return types.InlineKeyboardMarkup(row_width=4).add(*btns)


def playlist_choose_time(day: int) -> types.InlineKeyboardMarkup:
    btns = [
        types.InlineKeyboardButton(get_broadcast_name(time=time),
                                   callback_data=_parse(CB.PLAYLIST, CB.TIME, day, time))
        for time in BROADCAST_TIMES_[day]
    ]
    btns.append(types.InlineKeyboardButton(_btns_text.BACK, callback_data=_parse(CB.PLAYLIST, CB.BACK)))
    return types.InlineKeyboardMarkup(row_width=3).add(*btns)


#

_EMOJI_NUMBERS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")


async def playlist_move(playback: List[playlist.PlaylistItem] = None):
    if playback is None:
        playback = await playlist.get_next()
    btns = [
        types.InlineKeyboardButton(
            f"{_EMOJI_NUMBERS[i]} 🕖{track.time_start.strftime('%H:%M:%S')} {track.title.ljust(120)}.",
            callback_data=_parse(CB.PLAYLIST, CB.MOVE, track.index, track.time_start.timestamp())
        )
        for i, track in enumerate(playback[:10])
    ]
    btns.append(types.InlineKeyboardButton(f"🔄Обновить", callback_data=_parse(CB.PLAYLIST, CB.MOVE, -1, 0, 0)))
    return types.InlineKeyboardMarkup(row_width=1).add(*btns)
