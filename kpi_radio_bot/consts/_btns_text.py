from enum import IntEnum

CALLBACKS = IntEnum("CALLBACKS", (
    'ORDER', 'PLAYLIST', 'OTHER',
    'DAY', 'TIME', 'BACK', 'CANCEL', 'NOTIME', 'MODERATE', 'UNMODERATE',
    'NEXT', 'MOVE', 'HELP',

))

STATUS = IntEnum("STATUS", ('QUEUE', 'NOW', 'REJECT'))


class MENU:
    ORDER = '📝Заказать песню'
    WHAT_PLAYING = '🎧Что играет?'
    HELP = '⁉️Помощь'
    TIMETABLE = '⏱Расписание эфиров'
    FEEDBACK = '🖌Обратная связь'


HELP = {
    'orders': '📝Заказ песни',
    'criteria': '❗Модерация',
    'playlist': '⏭Плейлист',
    'feedback': '🖌Обратная связь'
}

INLINE_SEARCH = 'Удобный поиск'

HISTORY = 'Что играло'
NEXT = 'Что будет играть'

BACK = 'Назад'
CANCEL = 'Отмена'

QUEUE = '✅Принять'
NOW = 'Сейчас'
REJECT = '❌Отклонить'

BAD_ORDER_BUT_OK = 'Все ок'
