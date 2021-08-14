from pathlib import Path

from consts.config import IS_TEST_ENV, PATH_ROOT

HISTORY_CHANNEL_LINK = 'https://t.me/rkpi_music'

BAD_WORDS = [
    'пизд',
    'бля',
    'хуй', 'хуя', 'хуи', 'хуе',
    'жирный член',
    'ебать', 'еби', 'ебло', 'ебля', 'ебуч',
    'долбо',
    'дрочит',
    'мудак', 'мудило',
    'пидор', 'пидар',
    'сука', 'суку',
    'гандон',
    'fuck', 'bitch', 'shit', 'dick', 'cunt'
]

ANIME_WORDS = ['anime', 'аниме', 'tvアニメ', 'japan']

BAD_NAMES = [
    'корж', 'тима', 'стрыкало', 'нервы', 'гречка', 'morgenstern', 'face', 'gspd',
    'gachi', '♂', 'slave', 'ass', 'butt', 'right version',
    'remix', 'radio tapok',
]

WEEK_DAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
NEXT_DAYS = ['Сегодня', 'Завтра', 'Послезавтра', 'Послепослезавтра', 'Сейчас']
TIMES = ['Утренний эфир', 'Первый перерыв', 'Второй перерыв', 'Третий перерыв', 'Четвертый перерыв', 'Вечерний эфир']


BROADCAST_TIMES_NORMAL = {  # короче эту тему лучше сделать как функцию геттер имхо
    #  day:
    #       num:  start, stop

    **dict.fromkeys(  # same value for many keys
        [0, 1, 2, 3, 4, 5],
        {
            0: ('08:00', '08:30'),
            1: ('10:05', '10:25'),
            2: ('12:00', '12:20'),
            3: ('13:55', '14:15'),
            4: ('15:50', '16:10'),
            5: ('18:00', '22:00'),
        }
    ),

    6: {
        0: ('12:00', '18:00'),
        5: ('18:00', '22:00')
    }

}

BROADCAST_TIMES_VACATION = {
    **dict.fromkeys(
        [0, 1, 2, 3, 4, 5, 6],
        {
            0: ('9:00', '13:00'),
            5: ('13:00', '22:00')
        }
    ),
}

BROADCAST_TIMES = BROADCAST_TIMES_VACATION


class PATHS:
    _BASE = Path('/music') if not IS_TEST_ENV else PATH_ROOT / 'music'
    ORDERS = _BASE / 'orders'  # сюда бот кидает заказанные песни
    ARCHIVE = _BASE / 'archive'  # сюда песни перемещаются каждую ночь с папки заказов
    # ETHER = _BASE / 'Эфир'  # тут песни выбранные радистами, не используется
