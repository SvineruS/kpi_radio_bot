import logging
from datetime import datetime
from aiogram import types
from config import *
import bot_utils
import ban
import music_api
import playlist_api
import keyboards
import consts


async def predlozka_day(query, day: int):
    await bot.edit_message_caption(
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        caption=consts.times_name['week_days'][day] + ', отлично. Теперь выбери время',
        reply_markup=keyboards.choice_time(day)
    )


async def predlozka_time(query, day: int, time: int):
    user = query.from_user
    name = bot_utils.get_audio_name(query.message.audio)

    is_ban = ban.chek_ban(user.id)
    if is_ban:
        return await bot.send_message(query.message.chat.id, "Вы не можете предлагать музыку до " +
                                      datetime.fromtimestamp(is_ban).strftime("%d.%m %H:%M"))

    admin_keyboard = keyboards.admin(day, time, name, user.id)
    now = bot_utils.is_break_now(day, time)
    text_datetime = consts.times_name['week_days'][day] + ', ' + bot_utils.get_break_name(time)
    text_admin = ('‼️' if now else '❗️') + \
                 'Новый заказ - ' + text_datetime + \
                 (' (сейчас!)' if now else '') + \
                 ' от ' + bot_utils.get_user_name(user)

    await bot.edit_message_caption(
        caption=consts.text['predlozka_moderating'].format(text_datetime),
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        reply_markup=types.InlineKeyboardMarkup()
    )

    await bot.send_message(user.id, consts.text['menu'], reply_markup=keyboards.start)

    await bot.send_audio(ADMINS_CHAT_ID, query.message.audio.file_id, text_admin,
                         reply_markup=admin_keyboard)


async def admin_cancel(query, day: int, time: int, status: bool):
    user = query.message.caption_entities[0].user
    name = bot_utils.get_audio_name(query.message.audio)

    admin_keyboard = keyboards.admin(day, time, name, user.id)
    now = bot_utils.is_break_now(day, time)
    text_datetime = consts.times_name['week_days'][day] + ', ' + bot_utils.get_break_name(time)
    text_admin = ('‼️' if now else '❗️') + \
                 'Новый заказ - ' + text_datetime + \
                 (' (сейчас!)' if now else '') + \
                 ' от ' + bot_utils.get_user_name(user)

    await bot.edit_message_caption(caption=text_admin, chat_id=ADMINS_CHAT_ID,
                                   message_id=query.message.message_id,
                                   reply_markup=admin_keyboard)

    if status:
        path = bot_utils.get_music_path(day, time) / (name + '.mp3')

        for i in await music_api.radioboss_api(action='getplaylist2'):  # удалить из плейлиста радиобосса
            if i.attrib['FILENAME'] == str(path):
                await music_api.radioboss_api(action='delete', pos=i.attrib['INDEX'])
                break
        bot_utils.delete_file(path)  # удалить с диска


async def admin_check_text(query):
    name = bot_utils.get_audio_name(query.message.audio)
    text = await music_api.search_text(name)
    if not text:
        return await bot.answer_callback_query(query.id, text="Не нашел текст")
    bad_words = bot_utils.check_bad_words(text)
    return await bot.answer_callback_query(query.id, text=bad_words)


async def admin_choice(query, status: bool, user_id, day: int, time: int):
    name = bot_utils.get_audio_name(query.message.audio)

    new_text = 'Заказ: ' + query.message.caption.split(' - ')[1].split(' от')[0] + \
               ', от ' + bot_utils.get_user_name(query.message.caption_entities[0].user) + \
               ' - ' + ("✅Принят" if status else "❌Отклонен") + \
               ' (' + bot_utils.get_user_name(query.from_user) + ')'

    keyboard_cancel = types.InlineKeyboardMarkup()
    keyboard_cancel.add(types.InlineKeyboardButton(
        text='Отмена',
        callback_data='-|-'.join(['admin_cancel', str(day), str(time), 'ok' if status else 'neok'])
    ))

    await bot.edit_message_caption(caption=new_text,
                                   chat_id=query.message.chat.id, message_id=query.message.message_id,
                                   reply_markup=keyboard_cancel
                                   )

    if status:
        to = bot_utils.get_music_path(day, time) / (name + '.mp3')
        bot_utils.create_dirs(to)

        await query.message.audio.download(to, timeout=60)
        await playlist_api.write_sender_tag(to, query.message.caption_entities[0].user)

        if bot_utils.is_break_now(day, time):
            data = await playlist_api.get_suggestion_data()  # получаем позицию [0] и время ожидания [1]
            waiting_time = str(data[1]) + bot_utils.case_by_num(data[1], ' минуту', ' минуты', ' минут')
            msg = consts.text['predlozka_ok_next'].format(
                name, 'прямо сейчас!' if data[0] == -2 else f'примерно через {waiting_time}')

            await music_api.radioboss_api(action='inserttrack', filename=to, pos=data[0])
            await bot.edit_message_caption(caption=new_text + f"\nОжидание: {waiting_time}",
                                           chat_id=query.message.chat.id, message_id=query.message.message_id,
                                           reply_markup=keyboard_cancel
                                           )
            await bot.send_message(user_id, msg)
        else:
            await bot.send_message(user_id, consts.text['predlozka_ok'].format(name))
    else:
        await bot.send_message(user_id, consts.text['predlozka_neok'].format(name))


async def predlozka_day_back(query):
    await bot.edit_message_caption(
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        caption='Выбери день', reply_markup=keyboards.choice_day()
    )


async def predlozka_cancel(query):
    await bot.edit_message_caption(
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        caption='Ну ок(', reply_markup=types.InlineKeyboardMarkup()
    )
    await bot.send_message(query.message.chat.id, consts.text['menu'], reply_markup=keyboards.start)


async def song_now(message):
    playback = await playlist_api.get_now()
    if not playback:
        await bot.send_message(message.chat.id, "Не знаю(", reply_markup=keyboards.what_playing)
    else:
        await bot.send_message(message.chat.id, consts.text['what_playing'].format(*playback),
                               reply_markup=keyboards.what_playing)


async def song_prev(query):
    playback = await playlist_api.get_prev()
    if not playback:
        return await bot.send_message(query.message.chat.id, consts.text['song_no_prev'])
    text = song_format(playback)
    await bot.send_message(query.message.chat.id, text)


async def song_next(query):
    playback = await playlist_api.get_next()
    if not playback:
        return await bot.send_message(query.message.chat.id, consts.text['song_no_next'])
    text = song_format(playback)
    await bot.send_message(query.message.chat.id, text)


def song_format(playback):
    text = [
        f"🕖<b>{datetime.strftime(track['time_start'], '%H:%M:%S')}</b> {track['title']}"
        for track in playback
    ]
    return '\n'.join(text)


async def help_change(query, key):
    try:
        await bot.edit_message_text(consts.help[key], query.message.chat.id, query.message.message_id,
                                    reply_markup=keyboards.choice_help)
    except:
        pass


async def admin_reply(message):
    if message.text and message.text.startswith("!"):  # игнор ответа
        return

    to = txt = None
    if message.reply_to_message.audio:  # на заказ
        to = message.reply_to_message.caption_entities[0].user.id
        txt = "На ваш заказ <i>(" + bot_utils.get_audio_name(message.reply_to_message.audio) + ")</i> ответили:"

    if message.reply_to_message.forward_from:  # на отзыв
        to = message.reply_to_message.forward_from.id
        txt = "На ваше сообщение ответили: "

    await bot.send_message(to, txt)

    if message.audio:
        await bot.send_audio(to, message.audio.file_id)
    elif message.sticker:
        await bot.send_sticker(to, message.sticker.file_id)
    elif message.photo:
        await bot.send_photo(to, message.photo[-1].file_id, caption=message.caption)
    else:
        await bot.send_message(to, message.text, parse_mode='markdown')


async def search_audio(message):
    await bot.send_chat_action(message.chat.id, 'upload_audio')
    audio = await music_api.search(message.text)

    if not audio:
        await bot.send_message(message.chat.id, 'Ничего не нашел( \n'
                                                'Можешь загрузить свое аудио сам или переслать от другого бота!',
                               reply_markup=keyboards.start)
    else:
        audio = audio[0]
        try:
            await bot.send_audio(
                message.chat.id,
                music_api.get_download_url(audio['url'], audio['artist'], audio['title']),
                'Выбери день (или отредактируй название)',
                reply_markup=keyboards.choice_day()
            )

        except Exception as ex:
            logging.error(f'send audio: {ex} {audio["url"]}')
            await bot.send_message(message.chat.id, consts.text['error'], reply_markup=keyboards.start)


async def inline_search(inline_query):
    name = inline_query.query
    music = await music_api.search(name)
    if not music:
        return await bot.answer_inline_query(inline_query.id, [])

    articles = []
    for i in range(min(50, len(music))):
        audio = music[i]
        if not audio or not audio['url']:
            continue
        articles.append(
            types.InlineQueryResultAudio(
                id=str(hash(audio['url'])),
                audio_url=music_api.get_download_url(audio['url'], audio['artist'], audio['title']),
                performer=audio['artist'],
                title=audio['title']
            )
        )
    await bot.answer_inline_query(inline_query.id, articles)


async def admin_ban(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return
    if message.reply_to_message is None:
        return await bot.send_message(message.chat.id, "Перешлите сообщение пользователя, которого нужно забанить")

    cmd = message.text.split(' ')
    user = message.reply_to_message.caption_entities[0].user if message.reply_to_message.audio else \
        message.reply_to_message.forward_from
    ban_time = int(cmd[1]) if len(cmd) >= 2 else \
        60 * 24
    reason = (" Бан по причине: <i>" + ' '.join(cmd[2:]) + "</i>") if len(cmd) >= 3 else ""
    ban_time = str(ban.ban_user(user.id, ban_time))

    if ban_time == "0":
        await bot.send_message(message.chat.id, "Пользователь " + bot_utils.get_user_name(user) + " разбанен")
    else:
        await bot.send_message(message.chat.id, "Пользователь " + bot_utils.get_user_name(user)
                               + " забанен на " + ban_time + " минут." + reason)
        await bot.send_message(user.id, "Вы были забанены на " + ban_time + " минут." + reason)


async def send_history(fields):
    if not fields['artist'] and not fields['title']:
        fields['title'] = fields['casttitle']

    sender_name = await playlist_api.read_sender_tag(fields['path'])
    sender_name = 'Заказал(а) ' + sender_name if sender_name else 'От команды РадиоКпи'

    f = open(fields['path'], 'rb')
    await bot.send_audio(HISTORY_CHAT_ID, f, sender_name,
                         performer=fields['artist'], title=fields['title'])
    f.close()


async def send_live_begin(time):
    await bot.send_message(HISTORY_CHAT_ID, bot_utils.get_break_name(time))
