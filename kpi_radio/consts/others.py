from pathlib import Path

from consts.config import IS_TEST_ENV, PATH_ROOT

HISTORY_CHANNEL_LINK = 'https://t.me/rkpi_music'

BAD_WORDS = [
    'пизд',
    'пізд',
    'бля',
    'хуй', 'хуя', 'хуи', 'хуе',
    'жирный член',
    'ебать', 'еби', 'ебло', 'ебля', 'ебуч',
    'єбать', 'єбати', 'єби', 'єбло', 'єбля', 'єбуч',
    'їбать', 'їбати', 'їби', 'їбло', 'їбля', 'їбуч',
    'долбо',
    'дрочит',
    'мудак', 'мудило',
    'пидор', 'пидар',
    'підор', 'підар',
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

WEEK_DAYS = ['Понеділок', 'Вівторок', 'Середа', 'Четвер', 'Пʼятниця', 'Субота', 'Неділя']
NEXT_DAYS = ['Сьогодні', 'Завтра', 'Післязавтра', 'Післяпіслязавтра', 'Зараз']
ETHER_NAMES = ['Ранковий етер', 'Перша перерва', 'Друга перерва', 'Третя перерва', 'Четверта перерва', 'Вечірній етер']


ETHER_TIMES_NORMAL = {  # коротше цю тему краще зробити як функцію геттер імхо
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

ETHER_TIMES_VACATION = {
    **dict.fromkeys(
        [0, 1, 2, 3, 4, 5, 6],
        {
            0: ('9:00', '13:00'),
            5: ('13:00', '22:00')
        }
    ),
}

ETHER_TIMES = ETHER_TIMES_NORMAL

TIMETABLE_SECTIONS = {0: 'Будні', 6: 'Неділя'}


PATH_MUSIC = Path('/music') if not IS_TEST_ENV else PATH_ROOT / 'music'
