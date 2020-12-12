import json
from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from player import Broadcast
from consts import btns_text
from consts.btns_text import MENU, CALLBACKS as CB, STATUS
from consts.others import BROADCAST_TIMES_, HISTORY_CHANNEL_LINK, NEXT_DAYS, TIMES, WEEK_DAYS


class _CallbackDataBase:
    DATA: tuple = None

    def __init__(self, *args):
        if len(args) != len(self.DATA):
            raise Exception("Wrong callback data")
        for i, k in enumerate(self.DATA):
            self.__setattr__(k, args[i])
        self.data = args

    def __str__(self):
        return json.dumps((self.__class__.__name__, *self.data))

    @classmethod
    def from_str(cls, query_data: str):
        try:
            data = json.loads(query_data)
        except json.JSONDecodeError:
            return None
        action, *data = data
        if action != cls.__name__:
            return None
        return cls(*data)

    @classmethod
    def c(cls, action, data=()):
        action = ''.join(map(str, map(int, action)))
        attrs = {
            'DATA': data,
            **{k: None for k in data}
        }
        return type(action, (cls, ), attrs)


CBOrderDay = _CallbackDataBase.c((CB.ORDER, CB.DAY), ('day', ))
CBOrderTime = _CallbackDataBase.c((CB.ORDER, CB.TIME), ('day', 'time'))
CBOrderNoTime = _CallbackDataBase.c((CB.ORDER, CB.NOTIME), ('day', 'attempts'))
CBOrderBack = _CallbackDataBase.c((CB.ORDER, CB.BACK))
CBOrderCancel = _CallbackDataBase.c((CB.ORDER, CB.CANCEL))
CBOrderModerate = _CallbackDataBase.c((CB.ORDER, CB.MODERATE), ('day', 'time', 'status'))
CBOrderUnModerate = _CallbackDataBase.c((CB.ORDER, CB.UNMODERATE), ('day', 'time', 'status'))

CBPlaylistNext = _CallbackDataBase.c((CB.PLAYLIST, CB.NEXT))
CBPlaylistDay = _CallbackDataBase.c((CB.PLAYLIST, CB.DAY), ('day', ))
CBPlaylistTime = _CallbackDataBase.c((CB.PLAYLIST, CB.TIME), ('day', 'time'))
CBPlaylistBack = _CallbackDataBase.c((CB.PLAYLIST, CB.BACK))
CBPlaylistMove = _CallbackDataBase.c((CB.PLAYLIST, CB.MOVE), ('index', 'start_time'))

CBOtherHelp = _CallbackDataBase.c((CB.OTHER, CB.HELP), ('key', ))

#


def _ikb(text: str, cb: _CallbackDataBase) -> InlineKeyboardButton:  # shortcut
    return InlineKeyboardButton(text, callback_data=str(cb))


ORDER_INLINE = InlineKeyboardMarkup().add(
    InlineKeyboardButton(btns_text.INLINE_SEARCH, switch_inline_query_current_chat="")
)

START = ReplyKeyboardMarkup(resize_keyboard=True).add(
    KeyboardButton(MENU.WHAT_PLAYING), KeyboardButton(MENU.ORDER)).add(
    KeyboardButton(MENU.FEEDBACK), KeyboardButton(MENU.HELP), KeyboardButton(MENU.TIMETABLE)
)

WHAT_PLAYING = InlineKeyboardMarkup(row_width=2).add(
    InlineKeyboardButton(btns_text.HISTORY, url=HISTORY_CHANNEL_LINK), _ikb(btns_text.NEXT, CBPlaylistNext())
)

CHOICE_HELP = InlineKeyboardMarkup(row_width=1).add(*[
    _ikb(help_value, CBOtherHelp(help_key))
    for help_key, help_value in btns_text.HELP.items()
])

BAD_ORDER_BUT_OK = InlineKeyboardMarkup(row_width=1).add(
    _ikb(btns_text.BAD_ORDER_BUT_OK, CBOrderBack()),
    _ikb(btns_text.CANCEL, CBOrderCancel())
)


#


async def order_choose_day() -> InlineKeyboardMarkup:
    today = datetime.today().weekday()
    btns = []

    if (broadcast_now := Broadcast.now()) and await broadcast_now.get_free_time() > 5:  # кнопка сейчас если эфир+влазит
        btns.append(_ikb(NEXT_DAYS[-1], CBOrderTime(today, broadcast_now.num)))

    if datetime.now().hour < 22:  # кнопка сегодня
        btns.append(_ikb(NEXT_DAYS[0], CBOrderDay(today)))

    for i in range(1, 4):  # завтра (1), послезавтра (2), послепослезавтра  (3)
        btns.append(_ikb(NEXT_DAYS[i], CBOrderDay((today + i) % 7)))

    btns.append(_ikb(btns_text.CANCEL, CBOrderCancel()))
    return InlineKeyboardMarkup(row_width=1).add(*btns)


async def order_choose_time(day: int, attempts: int = 5) -> InlineKeyboardMarkup:
    btns = []
    for num in BROADCAST_TIMES_[day]:
        broadcast = Broadcast(day, num)
        if broadcast.is_already_play_today():
            continue  # если сегодня и перерыв прошел - не добавляем кнопку

        free_minutes = await broadcast.get_free_time()

        if free_minutes == 0 and attempts > 0:
            btn = _ikb('❌' + TIMES[num], CBOrderNoTime(day, attempts))
        else:
            btn = _ikb(('⚠' if free_minutes < 5 else '') + TIMES[num], CBOrderTime(day, num))

        btns.append(btn)

    btns.append(_ikb(btns_text.BACK, CBOrderBack()))
    return InlineKeyboardMarkup(row_width=2).add(*btns)


#


def admin_moderate(broadcast: Broadcast) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(*[
        _ikb(text, CBOrderModerate(*broadcast, status))
        for status, text in {
            STATUS.QUEUE: btns_text.QUEUE,
            STATUS.NOW: btns_text.NOW,
            STATUS.REJECT: btns_text.REJECT
        }.items()
    ])


def admin_unmoderate(broadcast: Broadcast, status: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup().add(_ikb(btns_text.CANCEL, CBOrderUnModerate(*broadcast, status)))


#


def playlist_choose_day() -> InlineKeyboardMarkup:
    today = datetime.today().weekday()
    btns = []
    for day in range(4):
        day = (day + today) % 7
        btns.append(_ikb(WEEK_DAYS[day], CBPlaylistDay(day)))
    return InlineKeyboardMarkup(row_width=4).add(*btns)


def playlist_choose_time(day: int) -> InlineKeyboardMarkup:
    btns = [
        _ikb(TIMES[time], CBPlaylistTime(day, time))
        for time in BROADCAST_TIMES_[day]
    ]
    btns.append(_ikb(btns_text.BACK, CBPlaylistBack()))
    return InlineKeyboardMarkup(row_width=3).add(*btns)


#

_EMOJI_NUMBERS = ("1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟")


async def playlist_move(pl=None):
    if pl is None:
        pl = await Broadcast.now().get_playlist_next()
    btns = [
        _ikb(
            f"{_EMOJI_NUMBERS[i]} 🕖{track.time_start.strftime('%H:%M:%S')} {track.title.ljust(120)}.",
            CBPlaylistMove(track.index_, track.time_start.timestamp())
        )
        for i, track in enumerate(pl[:10])
    ]
    btns.append(_ikb("🔄Обновить", CBPlaylistMove(-1, 0)))
    return InlineKeyboardMarkup(row_width=1).add(*btns)
