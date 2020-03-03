import json
from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from backend import playlist, Broadcast
from consts import btns_text
from consts.btns_text import MENU, CALLBACKS as CB, STATUS
from consts.others import BROADCAST_TIMES_, HISTORY_CHANNEL_LINK, NEXT_DAYS, TIMES, WEEK_DAYS


def _parse(*args) -> str:
    return json.dumps(args)


def unparse(data: str) -> dict:
    return json.loads(data)


def _ikb(text: str, *cb_data) -> InlineKeyboardButton:  # shortcut
    return InlineKeyboardButton(text, callback_data=_parse(*cb_data))


#


ORDER_INLINE = InlineKeyboardMarkup().add(
    InlineKeyboardButton(btns_text.INLINE_SEARCH, switch_inline_query_current_chat="")
)

START = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton(MENU.WHAT_PLAYING), KeyboardButton(MENU.ORDER)).add(
    KeyboardButton(MENU.FEEDBACK), KeyboardButton(MENU.HELP), KeyboardButton(MENU.TIMETABLE)
)

WHAT_PLAYING = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton(btns_text.HISTORY, url=HISTORY_CHANNEL_LINK),
    InlineKeyboardButton(btns_text.NEXT, callback_data=_parse(CB.PLAYLIST, CB.NEXT))
)

CHOICE_HELP = InlineKeyboardMarkup(row_width=1).add(*[
    _ikb(help_value, CB.OTHER, CB.HELP, help_key)
    for help_key, help_value in btns_text.HELP.items()
])

BAD_ORDER_BUT_OK = InlineKeyboardMarkup(row_width=1).add(
    _ikb(btns_text.BAD_ORDER_BUT_OK, CB.ORDER, CB.BACK),
    _ikb(btns_text.CANCEL, CB.ORDER, CB.CANCEL)
)


#


async def order_choose_day() -> InlineKeyboardMarkup:
    today = datetime.today().weekday()

    btns = []

    if (broadcast_now := Broadcast.now()) and await broadcast_now.get_free_time() > 5:  # кнопка сейчас если эфир+влазит
        btns.append(_ikb(NEXT_DAYS[-1], CB.ORDER, CB.TIME, today, broadcast_now.num))

    if datetime.now().hour < 22:  # кнопка сегодня
        btns.append(_ikb(NEXT_DAYS[0], CB.ORDER, CB.DAY, today))

    for i in range(1, 4):  # завтра (1), послезавтра (2), послепослезавтра  (3)
        btns.append(_ikb(NEXT_DAYS[i], CB.ORDER, CB.DAY, (today + i) % 7))

    btns.append(_ikb(btns_text.CANCEL, CB.ORDER, CB.CANCEL))
    return InlineKeyboardMarkup(row_width=1).add(*btns)


async def order_choose_time(day: int, attempts: int = 5) -> InlineKeyboardMarkup:
    btns = []
    for num in BROADCAST_TIMES_[day]:
        broadcast = Broadcast(day, num)
        if broadcast.is_already_play_today():
            continue  # если сегодня и перерыв прошел - не добавляем кнопку

        free_minutes = await broadcast.get_free_time()

        if free_minutes == 0 and attempts > 0:
            btn = _ikb(TIMES[num], CB.ORDER, CB.NOTIME, day, attempts)
        else:
            btn = _ikb(('⚠' if free_minutes < 5 else '') + TIMES[num], CB.ORDER, CB.TIME, day, num)

        btns.append(btn)

    btns.append(_ikb(btns_text.BACK, CB.ORDER, CB.BACK))
    return InlineKeyboardMarkup(row_width=2).add(*btns)


#


def admin_moderate(broadcast: Broadcast) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(*[
        _ikb(text, CB.ORDER, CB.MODERATE, *broadcast, status)
        for status, text in {
            STATUS.QUEUE: btns_text.QUEUE,
            STATUS.NOW: btns_text.NOW,
            STATUS.REJECT: btns_text.REJECT
        }.items()
    ])


def admin_unmoderate(broadcast: Broadcast, status: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(_ikb(btns_text.CANCEL, CB.ORDER, CB.UNMODERATE, *broadcast, status))


#


def playlist_choose_day() -> InlineKeyboardMarkup:
    today = datetime.today().weekday()
    btns = []
    for day in range(4):
        day = (day + today) % 7
        btns.append(_ikb(WEEK_DAYS[day], CB.PLAYLIST, CB.DAY, day))
    return InlineKeyboardMarkup(row_width=4).add(*btns)


def playlist_choose_time(day: int) -> InlineKeyboardMarkup:
    btns = [
        _ikb(TIMES[time], CB.PLAYLIST, CB.TIME, day, time)
        for time in BROADCAST_TIMES_[day]
    ]
    btns.append(_ikb(btns_text.BACK, CB.PLAYLIST, CB.BACK))
    return InlineKeyboardMarkup(row_width=3).add(*btns)


#

_EMOJI_NUMBERS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")


async def playlist_move(playback: playlist.PlayList = None):
    if playback is None:
        playback = await playlist.get_playlist_next()
    btns = [
        _ikb(
            f"{_EMOJI_NUMBERS[i]} 🕖{track.time_start.strftime('%H:%M:%S')} {track.title.ljust(120)}.",
            CB.PLAYLIST, CB.MOVE, track.index_, track.time_start.timestamp()
        )
        for i, track in enumerate(playback[:10])
    ]
    btns.append(_ikb(f"🔄Обновить", CB.PLAYLIST, CB.MOVE, -1, 0, 0))
    return InlineKeyboardMarkup(row_width=1).add(*btns)
