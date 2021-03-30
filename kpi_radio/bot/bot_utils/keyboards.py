from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from consts import btns_text
from consts.btns_text import STATUS, MENU
from consts.others import HISTORY_CHANNEL_LINK, NEXT_DAYS, TIMES, WEEK_DAYS, BROADCAST_TIMES
from player import Broadcast
from utils import DateTime
from . import _callbacks as cb


#


def _ikb(text: str, callback) -> InlineKeyboardButton:  # shortcut
    return InlineKeyboardButton(text, callback_data=str(callback))


ORDER_INLINE = InlineKeyboardMarkup().add(
    InlineKeyboardButton(btns_text.INLINE_SEARCH, switch_inline_query_current_chat="")
)

START = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton(MENU.WHAT_PLAYING), KeyboardButton(MENU.ORDER)
).add(
    KeyboardButton(MENU.FEEDBACK), KeyboardButton(MENU.HELP),
    KeyboardButton(MENU.TIMETABLE)
)

WHAT_PLAYING = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton(btns_text.HISTORY, url=HISTORY_CHANNEL_LINK), _ikb(btns_text.NEXT, cb.CBPlaylistNext())
)

CHOICE_HELP = InlineKeyboardMarkup(row_width=1).add(*[
    _ikb(help_value, cb.CBOtherHelp(help_key))
    for help_key, help_value in btns_text.HELP.items()
])

BAD_ORDER_BUT_OK = InlineKeyboardMarkup(row_width=1).add(
    _ikb(btns_text.BAD_ORDER_BUT_OK, cb.CBOrderBack()),
    _ikb(btns_text.CANCEL, cb.CBOrderCancel())
)


#


async def order_choose_day() -> InlineKeyboardMarkup:
    today = DateTime.day_num()
    btns = []

    if (broadcast_now := Broadcast.now()) and await broadcast_now.get_free_time() > 5:  # кнопка сейчас если эфир+влазит
        btns.append(_ikb(NEXT_DAYS[-1], cb.CBOrderTime(today, broadcast_now.num)))

    if DateTime.now().hour < 22:  # кнопка сегодня
        btns.append(_ikb(NEXT_DAYS[0], cb.CBOrderDay(today)))

    for i in range(1, 4):  # завтра (1), послезавтра (2), послепослезавтра  (3)
        btns.append(_ikb(NEXT_DAYS[i], cb.CBOrderDay((today + i) % 7)))

    btns.append(_ikb(btns_text.CANCEL, cb.CBOrderCancel()))
    return InlineKeyboardMarkup(row_width=1).add(*btns)


async def order_choose_time(day: int, attempts: int = 5) -> InlineKeyboardMarkup:
    btns = []
    for num in BROADCAST_TIMES[day]:
        broadcast = Broadcast(day, num)
        if broadcast.is_already_play_today():
            continue  # если сегодня и перерыв прошел - не добавляем кнопку

        free_minutes = await broadcast.get_free_time()

        if free_minutes == 0 and attempts > 0:
            btn = _ikb('❌' + TIMES[num], cb.CBOrderNoTime(day, attempts))
        else:
            btn = _ikb(('⚠' if free_minutes < 5 else '') + TIMES[num], cb.CBOrderTime(day, num))

        btns.append(btn)

    btns.append(_ikb(btns_text.BACK, cb.CBOrderBack()))
    return InlineKeyboardMarkup(row_width=2).add(*btns)


#


def admin_moderate(broadcast: Broadcast) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(*[
        _ikb(text, cb.CBOrderModerate(*broadcast, status))
        for status, text in {
            STATUS.QUEUE: btns_text.QUEUE,
            STATUS.NOW: btns_text.NOW,
            STATUS.REJECT: btns_text.REJECT
        }.items()
    ])


def admin_unmoderate(broadcast: Broadcast, status: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(_ikb(btns_text.CANCEL, cb.CBOrderUnModerate(*broadcast, status)))


#


def playlist_choose_day() -> InlineKeyboardMarkup:
    today = DateTime.day_num()
    btns = []
    for day in range(4):
        day = (day + today) % 7
        btns.append(_ikb(WEEK_DAYS[day], cb.CBPlaylistDay(day)))
    return InlineKeyboardMarkup(row_width=4).add(*btns)


def playlist_choose_time(day: int) -> InlineKeyboardMarkup:
    btns = [
        _ikb(TIMES[time], cb.CBPlaylistTime(day, time))
        for time in BROADCAST_TIMES[day]
    ] + [_ikb(btns_text.BACK, cb.CBPlaylistBack())]
    return InlineKeyboardMarkup(row_width=3).add(*btns)


#

_EMOJI_NUMBERS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")


async def playlist_move(pl=None):
    if pl is None:
        pl = await Broadcast.now().get_playlist_next()
    btns = [
        _ikb(
            f"{_EMOJI_NUMBERS[i]} 🕖{track.start_time.strftime('%H:%M:%S')} {track.title.ljust(120)}.",
            cb.CBPlaylistMove(track.index_, track.start_time.timestamp())
        )
        for i, track in enumerate(pl[:10])
    ] + [_ikb("🔄Обновить", cb.CBPlaylistMove(-1, 0))]
    return InlineKeyboardMarkup(row_width=1).add(*btns)
