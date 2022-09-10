START = 'Привіт, це бот Радіо КПІ.\n' \
        'Ти можеш:\n' \
        '📝Замовити пісню\n' \
        '🖌Поставити будь-яке запитання, що-небудь запропонувати, запропонувати свою кандидатуру до наших лав\n' \
        '🎧Дізнатися, що грає зараз, грало чи гратиме\n' \
        '⏱Дізнатися коли в улюбленому ЗВО перерви\n' \
        '\n⁉️Радимо насамперед прочитати інструкцію /help'

MENU = 'Вибери, що хочеш зробити 😜'

FEEDBACK = 'Пиши сюди все що хочеш чи реплай на повідомлення від нас і ми відповімо тобі) \n' \
           'Ну ще у нас є чат @rhub_kpi \n (⛔️/cancel)'
FEEDBACK_THANKS = 'Дякуємо за повідомлення!'

ORDER_CHOOSE_SONG = 'Що ти хочеш почути?\n' \
                    '➖ Напиши назву пісні та бот її знайде 🔎\n' \
                    '➖ Скинь посилання на трек із music.youtube.com\n' \
                    '➖ Завантаж або перейшли аудіофайл\n' \
                    '➖ Скористайтеся інлайн пошуком нижче\n' \
                    '➖ Використовуй інших ботів для пошуку та перейшли аудіо сюди (@vkm4bot, @LyBot)\n' \
                    '\n⛔️/cancel для скасування'

ORDER_INLINE_SEARCH = 'Натисни кнопку для інлайн-пошуку в нашому боті 👀'

CHOOSE_DAY = 'Вибери день'
CHOOSE_TIME = '{0}, відмінно. Тепер вибери час'

ORDER_ON_MODERATION = 'Дякуємо за замовлення ({0}), чекайте на модерацію!'
ORDER_ACCEPTED = 'Ваше замовлення "<b>{0}</b>", ({1}) прийняте!'
ORDER_ACCEPTED_UPNEXT = 'Ваше замовлення "<b>{0}</b>" прийняте та заграє {1}'
ORDER_ACCEPTED_TOOLATE = 'Мы хотели принять ваш заказ "<b>{0}</b>", ({1}), но он уже не влезет в эфир(( ' \
                             'Желаете перезаказ?'

ORDER_DENIED = 'Ваш заказ "<b>{0}</b>", ({1}) отклонен('

ORDER_CANCELED = 'Ну ок'

ORDER_PLAYING = 'Ваш заказ "<b>{0}</b>" заиграл! \n /notify - отключить уведомления'
ORDER_PEREZAKLAD = 'Ваш заказ не успел заиграть на этом эфире. Желаете перезаказ?'
ORDER_ERR_TOOLATE = 'На это время уже точно не успеет'
ORDER_ERR_TOOMUCH = 'Вы заказали слишком много треков на этот эфир'

HISTORY_TITLE = 'Заказал(а) {0}'

PLAYLIST_NOW = '⏮ <b>Предыдущий трек: </b> {0}\n' \
               '▶ <b>Сейчас играет: </b> {1}\n' \
               '⏭ <b>Следующий трек: </b> {2}'

PLAYLIST_NOW_NOTHING = 'На политехнической сейчас ничего не играет. Но зато играет на *вставить ссылку на ютуб*'  # todo

BAN_TRY_ORDER = 'Вы не можете предлагать музыку до {0}'
BAN_YOU_BANNED = 'Вы были забанены на {0}. {1}'

SEARCH_FAILED = 'Ничего не нашел( \n Можешь загрузить свое аудио сам или переслать от другого бота!'
ERROR = 'Не получилось('
UNKNOWN_CMD = 'Шо ты хош? Для заказа песни не забывай нажимать на кнопку "Заказать песню". Помощь тут /help'

SOMETHING_BAD_IN_ORDER = '<i>Упс..</i> Есть некоторая <b>вероятность</b>, что данный трек нарушает правила: \n' \
                         '{} \n\n Если вы считаете что все ок - нажмите кнопку "<code>Все ок</code>"'

BAD_ORDER_SHORT = 'Трек слишком короткий. (&lt;60 сек)'
BAD_ORDER_LONG = 'Трек слишком длинный (>6 мин.). Лучше не заказывать его на перерывы'
BAD_ORDER_BADWORDS = 'Трек вероятно содержит маты'
BAD_ORDER_ANIME = 'Трек вероятно является аниме опенингом'
BAD_ORDER_PERFORMER = 'Трек вероятно является "не форматом радио"'

HASHTAG_MODERATE = '#отмодерить'

HELP = {
    'orders': '''
📝Есть 3 способа <b>заказать песню:</b>

- Нажать на кнопку <code>Заказать песню</code> и ввести название, бот выберет наиболее вероятный вариант

- Использовать инлайн режим поиска (ввести <code>@kpiradio_bot</code> или нажать на соответствующую кнопку).
    В этом случае ты можешь выбрать из 50 найденных вариантов, с возможностью сначала послушать

- Загрузить или переслать боту желаемую песню
После этого необходимо выбрать день и время для заказа.''',

    'criteria': '''
✅ Приветствуются нейтральные, спокойные песни, которые не будут отвлекать от учебного процесса.

⚠️ Пожалуйста, не заказывайте много песен сразу. Не заказывайте больше 1 трека на эфир, кроме вечернего.

❌ Отклоняются:
    - битые треки, треки длиной менее 1 минуты
    - треки длиной более 6 минут, кроме вечернего эфира
    - лайвы, ремиксы плохого качества
    - дважды и более заказанный трек на один эфир
    - треки с матами, нехорошим смыслом
    - треки с несоответствующим названием
    - не формат радио (см. ниже)

Сколько людей, столько и вкусов. Но мы чаще всего отклоняем:
    - русский рэп
    - треки с элементами скрима, жёсткого металла
    - гачи, стоны, аниме опенинги
    - каверы (radio tapok)
    - таких исполнителей как Корж, Команда Белоруских и подобные

❗️ Рупора радио - не колонки в клубе. Помните об этом.
️Модераторы в праве отклонить ваш трек без объяснения причин.''',

    'playlist': '''
<b>⏭Плейлист радио:</b>

- Узнать что играет сейчас, играло до этого или будет играть можно нажав на кнопку "<code>Что играет</code>"

- Помните дату и время когда играла песня и хотите ее найти? Можете найти ее там же - "<code>Что играло?</code>"

- Хотите узнать что будет играть в будущем? "<code>Что будет играть</code>"!

- Заказ <b>одноразовый</b>. Если ваша песня не успела войти в эфир - <b>перезакажите на следующий раз</b>.''',

    'feedback': '''
  <b>🖌Обратная связь:</b>

- Вы всегда можете написать команде админов что вы думаете о них и о радио

- Если хотите стать частью радио - пишите об этом и готовьтесь к анкетам

- Считаете что то неудобным? Есть предложения по улучшению? Не задумываясь пиши нам.

- У нас есть чат @rhub_kpi''',

    'start': 'Выберите интересующую вас тему. (Советуем прочитать все)'
}
