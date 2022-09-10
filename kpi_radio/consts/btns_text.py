from enum import IntEnum

CALLBACKS = IntEnum.__call__("CALLBACKS", (
    'ORDER', 'PLAYLIST', 'OTHER',
    'DAY', 'TIME', 'BACK', 'CANCEL', 'NOTIME', 'MODERATE', 'UNMODERATE',
    'NEXT', 'MOVE', 'HELP',

))

STATUS = IntEnum.__call__("STATUS", ('QUEUE', 'NOW', 'REJECT'))


class MENU:
    ORDER = '📝 Замовити пісню'
    WHAT_PLAYING = '🎧 Що грає?'
    HELP = '⁉️ Допомога'
    TIMETABLE = '⏱ Розклад етерів'
    FEEDBACK = '🖌 Зворотній звʼязок'


HELP = {
    'orders': '📝 Замовлення пісні',
    'criteria': '❗ Модерація',
    'playlist': '⏭ Плейлист',
    'feedback': '🖌 Зворотній звʼязок'
}

INLINE_SEARCH = 'Зручний пошук'

HISTORY = 'Що грало'
NEXT = 'Що гратиме'

BACK = 'Назад'
CANCEL = 'Відміна'

QUEUE = '✅ Прийняти'
NOW = 'Зараз'
REJECT = '❌ Відхилити'

BAD_ORDER_BUT_OK = 'Все ок'
