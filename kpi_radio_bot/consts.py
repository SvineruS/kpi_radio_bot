from pathlib import Path


class TextConstants:
    START = 'Привет, это бот РадиоКПИ.\n' \
            'Ты можешь:\n' \
            ' - 📝Заказать песню\n' \
            ' - 🖌Задать любой вопрос, что-нибудь предложить, предложить свою кандидатуру в наши ряды\n' \
            ' - 🎧Узнать, что играет сейчас, играло или будет играть\n' \
            ' - ⏱Узнать когда в любимом вузе перерывы' \
            '\n\n' \
            '⁉️Советуем первым делом прочитать инструкцию /help'
    MENU = 'Выбери, что хочешь сделать 😜'
    FEEDBACK = 'Пиши сюда все что хочешь или реплай на сообщение от нас на и мы ответим тебе) \n' \
               'Ну еще у нас есть чат @rhub_kpi \n (⛔️/cancel)'
    FEEDBACK_THANKS = 'Спасибо за сообщение!'

    ORDER_CHOOSE_SONG = 'Что ты хочешь услышать? Напиши название или скинь свою песню\n(⛔️/cancel)'
    ORDER_INLINE_SEARCH = 'Нажми на кнопку для инлайн-поиска в нашем боте 👀 \n' \
                          'По желанию можно использовать сторонних ботов, например @vkm4bot 🤷‍♀️'
    ORDER_CHOOSE_DAY = 'Теперь выбери день'
    ORDER_CHOOSE_TIME = '{0}, отлично. Теперь выбери время'
    ORDER_ON_MODERATION = 'Спасибо за заказ ({0}), ожидайте модерации!'
    ORDER_ACCEPTED = 'Ваш заказ "<b>{0}</b>", ({1}) принят!'
    ORDER_ACCEPTED_UPNEXT = 'Ваш заказ "<b>{0}</b>" принят и заиграет {1}'
    ORDER_ERR_DENIED = 'Ваш заказ "<b>{0}</b>", ({1}) отклонен('
    ORDER_ERR_ACCEPTED_TOOLATE = 'Мы хотели принять ваш заказ "<b>{0}</b>", ({1}), но он уже не влезет в эфир(( ' \
                                 'Желаете перезаказ?'
    ORDER_PLAYING = 'Ваш заказ "<b>{0}</b>" заиграл! \n /notify - отключить уведомления'
    ORDER_PEREZAKLAD = 'Ваш заказ не успел заиграть на этом эфире. Желаете перезаказ?'
    ORDER_ERR_TOOLATE = 'На это время уже точно не успеет'

    HISTORY_TITLE = 'Заказал(а) {0}'

    WHAT_PLAYING = '⏮ <b>Предыдущий трек: </b> {0}\n' \
                   '▶ <b>Сейчас играет: </b> {1}\n' \
                   '⏭ <b>Следующий трек: </b> {2}'

    SONG_NO_NOW = 'На политехнической сейчас ничего не играет. Но зато играет на *вставить ссылку на ютуб*'  # todo
    SONG_NO_NEXT = 'Доступно только во время эфира'

    BAN_TRY_ORDER = 'Вы не можете предлагать музыку до {0}'
    BAN_YOU_BANNED = 'Вы были забанены на {0}. {1}'

    SEARCH_FAILED = 'Ничего не нашел( \n Можешь загрузить свое аудио сам или переслать от другого бота!'
    ERROR = 'Не получилось('
    UNKNOWN_CMD = 'Шо ты хош? Для заказа песни не забывай нажимать на кнопку "Заказать песню". Помощь тут /help'
    ORDER_CANCELED = 'Ну ок'

    HELP = {
        'orders': '''
📝Есть 3 способа <b>заказать песню:</b>
- Нажать на кнопку <code>Заказать песню</code> и ввести название, бот выберет наиболее вероятный вариант
- Использовать инлайн режим поиска (ввести <code>@kpiradio_bot</code> или нажать на соответствующую кнопку). 
    В этом случае ты можешь выбрать из 50 найденных вариантов, с возможностью сначала послушать
- Загрузить или переслать боту желаемую песню
После этого необходимо выбрать день и время для заказа.''',

        'criteria': '''
 <b>❗️Советы:</b>
- Не отправляйте слишком много песен сразу, их все еще принимают люди, а не нейросети
- Учтите, что у песен с нехорошими словами или смыслом высокий шанс не пройти модерацию.
- Приветствуются песни на украинском <i>(гугл "квоты на радио")</i>
- Не приветствуется Корж и подобные ему.
- Приветствуются нейтральные, спокойные песни, которые не будут отвлекать от учебного процесса ''',

        'playlist': '''
<b>⏭Плейлист радио:</b>
- Узнать что играет сейчас, играло до этого или будет играть можно нажав на кнопку <code>Что играет</code>
- Помните дату и время когда играла песня и хотите ее найти? Можете найти ее там же <code>История</code>
- Заказ <b>одноразовый</b>. Если ваша песня не успела войти в эфир - закажите <b>на следующий раз</b>.''',

        'feedback': '''
  <b>🖌Обратная связь:</b>
- Вы всегда можете написать команде админов что вы думаете о них и о радио
- Если хотите стать частью радио - пишите об этом и готовьтесь к анкетам
- Считаете что то неудобным? Есть предложения по улучшению? Не задумываясь пиши нам.
- У нас есть чат @rhub_kpi''',

        'start': 'Выберите интересующую вас тему. (Советуем прочитать все)'
    }


class BtnConstants:
    MENU = {
        'order': '📝Заказать песню',
        'what_playing': '🎧Что играет?',
        'help': '⁉️Помощь',
        'timetable': '⏱Расписание эфиров',
        'feedback': '🖌Обратная связь',
    }

    HELP = {
        'orders': '📝Заказ песни',
        'criteria': '❗Модерация',
        'playlist': '⏭Тонкости плейлиста',
        'feedback': '🖌Обратная связь'
    }

    HISTORY = 'Что играло'
    NEXT = 'Что будет играть'

    BACK = 'Назад'
    CANCEL = 'Отмена'

    QUEUE = '✅Принять'
    NOW = 'Сейчас'
    REJECT = '❌Отклонить'


bad_words = [
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

anime_words = ['anime', 'аниме']

times_name = {
    'week_days': ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'],
    'next_days': ['Сегодня', 'Завтра', 'Послезавтра', 'Послепослезавтра', 'Сейчас'],
    'times': ['Утренний эфир', 'Первый перерыв', 'Второй перерыв', 'Третий перерыв', 'Четвертый перерыв',
              'Вечерний эфир'],
}

stats_blacklist = ['svinerus', 'mnb3000', 'MrRipll',
                   'eddienubes', 'deshtone', 'shpiner',
                   'nastyakulish', 'HomelessAtomist', 'Da_Yanchyk']

broadcast_times = {  # todo короче эту тему лучше сделать как функцию геттер имхо
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
            5: ('17:50', '22:00'),
        }
    ),

    6: {
        0: ('12:00', '18:00'),
        5: ('18:00', '22:00')
    }

}

paths = {
    'orders': Path('D:/Вещание Радио/Заказы'),  # сюда бот кидает заказанные песни
    'archive': Path('D:/Вещание Радио/Архив'),  # сюда песни перемещаются каждую ночь с папки заказов
    'ether': Path('D:/Вещание Радио/Эфир'),  # тут песни выбранные радистами, не используется
}


# летние пути
# paths = {
#     'orders': Path('D:/Вещание Радио/Летний эфир/Заказы'),
#     'archive': Path('D:/Вещание Радио/Летний эфир/Архив'),
#     'ether': Path('D:/Вещание Радио/Летний эфир/Эфир'),
# }


def _time(s):
    h, m = s.split(':')
    return int(h) * 60 + int(m)


broadcast_times_ = {
    day_k: {
        num_k: tuple(_time(time) for time in num_v)
        for num_k, num_v in day_v.items()
    } for day_k, day_v in broadcast_times.items()
}
