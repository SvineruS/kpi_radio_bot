from pathlib import Path


text = {
    'start': '''Привет, это бот РадиоКПИ. 
Ты можешь:
 - Заказать песню   
 - Задать любой вопрос
 - Узнать, что играет сейчас, играло или будет играть
 - Узнать, как стать частью ламповой команды РадиоКПИ.

⁉️Советуем первым делом прочитать инструкцию /help''',

    'menu': 'Выбери, что хочешь сделать 😜',

    'feedback': 'Ты можешь оставить отзыв о работе РадиоКПИ или предложить свою кандидатуру для вступления в наши ряды!'
                '\nНапиши сообщение и админы ответят тебе! \n(⛔️/cancel)',
    'feedback_thanks': 'Спасибо за заявку, мы обязательно рассмотрим ее!',

    'order_choose_song': 'Что ты хочешь услышать? Напиши название или скинь свою песню\n(⛔️/cancel)',
    'order_inline_search': 'Нажми на кнопку для инлайн-поиска в нашем боте 👀 \n'
                           'По желанию можно использовать сторонних ботов, например @vkm4bot 🤷‍♀️',

    'order_choose_day': 'Теперь выбери день',
    'order_choose_time': '{0}, отлично. Теперь выбери время',

    'order_moderating': 'Спасибо за заказ ({0}), ожидайте модерации!',
    'order_ok': 'Ваш заказ ({0}) принят!',
    'order_ok_next': 'Ваш заказ ({0}) принят и заиграет {1}',
    'order_ok_but_notime': 'Мы хотели принять ваш заказ {0}, но он уже не влезет в эфир((',
    'order_neok': 'Ваш заказ ({0}) отклонен(',

    'order_notime': 'На это время уже точно не успеет',

    'what_playing': '⏮ <b>Предыдущий трек: </b> {0}\n'
                    '▶ <b>Сейчас играет: </b> {1}\n'
                    '⏭ <b>Следующий трек: </b> {2}',

    'song_no_prev': 'Не знаю( Используй историю 🤷‍♀️',
    'song_no_next': 'Доступно только во время эфира',

    'error': 'Не получилось(',
    'unknown_cmd': 'Шо ты хош? Для заказа песни не забывай нажимать на кнопку "Заказать песню". Помощь тут /help',
}


helps = {
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
- Если вы заказываете песню во время эфира, мы постараемся сделать так, что бы она заиграла следующей
- Заказ <b>одноразовый</b>. Если ваша песня не успела войти в эфир - закажите <b>на следующий раз</b>.''',

    'feedback': '''
  <b>🖌Обратная связь:</b>
- Вы всегда можете написать команде админов что вы думаете о них и о радио
- Если хотите стать частью радио - пишите об этом и готовьтесь к анкетам
- Считаете что то неудобным? Есть предложения по улучшению? Не задумываясь пиши нам.
- У нас есть чат @rhub_kpi''',

    'btns': {
        'orders': '📝Заказ песни',
        'criteria': '❗Модерация',
        'playlist': '⏭Тонкости плейлиста',
        'feedback': '🖌Обратная связь'
    },
    'first_msg': 'Выберите интересующую вас тему. (Советуем прочитать все)',
}

bad_words = [
    'пизд',
    'бля',
    'хуй', 'хуя', 'хуи', 'хуе',
    'ебать', 'еби', 'ебло', 'ебля', 'ебуч',
    'долбо',
    'дрочит',
    'мудак', 'мудило',
    'пидор', 'пидар',
    'сука', 'суку',
    'гандон',
    'fuck', 'bitch', 'shit', 'dick'
]

times_name = {
    'week_days': ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'],
    'next_days': ['Сегодня', 'Завтра', 'Послезавтра', 'Сейчас'],
    'times': ['Утренний эфир', 'Первый перерыв', 'Второй перерыв', 'Третий перерыв', 'Четвертый перерыв',
              'Вечерний эфир'],
}

broadcast_times = {
    #  num  start     stop
    'sunday': {
        0: ('11:15', '18:00'),
        5: ('18:00', '22:00')
    },
    'elseday': {
        0: ('8:00', '8:30'),
        1: ('10:05', '10:25'),
        2: ('12:00', '12:20'),
        3: ('13:55', '14:15'),
        4: ('15:50', '16:10'),
        5: ('17:50', '22:00'),
    }
}

paths = {
    'orders': Path('D:/Вещание Радио/Заказы'),
    'archive': Path('D:/Вещание Радио/Архив'),
    'ether': Path('D:/Вещание Радио/Эфир'),
}


def _time(s):
    h, m = s.split(':')
    return int(h)*60 + int(m)


broadcast_times_ = {
    day_k: {
        num_k: tuple(_time(time) for time in num_v)
        for num_k, num_v in day_v.items()
    } for day_k, day_v in broadcast_times.items()
}
