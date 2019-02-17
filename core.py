import asyncio
import logging
import urllib.parse
from datetime import datetime
from aiogram import types
from config import *
import bot_utils
import ban
import music_api
import playlist_api


async def predlozka_day(query, day: int):
    await bot.edit_message_caption(
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        caption=bot_utils.TEXT['days1'][day] + ', отлично. Теперь выбери время',
        reply_markup=bot_utils.keyboard_time(day)
    )


async def predlozka_time(query, day: int, time: int):
    user = query.from_user
    name = bot_utils.get_audio_name(query.message.audio)

    is_ban = ban.chek_ban(user.id)
    if is_ban:
        return await bot.send_message(query.message.chat.id, "Вы не можете предлагать музыку до " +
                                      datetime.fromtimestamp(is_ban).strftime("%d.%m %H:%M"))

    admin_keyboard = bot_utils.keyboard_admin(day, time, name, user.id)
    now = bot_utils.is_break_now(day, time)
    text_datetime = bot_utils.TEXT['days1'][day] + ', ' + bot_utils.get_break_name(time)
    text_admin = ('‼️' if now else '❗️') + \
                 'Новый заказ - ' + text_datetime + \
                 (' (сейчас!)' if now else '') + \
                 ' от ' + bot_utils.get_user_name(user)

    await bot.edit_message_caption(
        caption=bot_utils.TEXT['predlozka_moderating'].format(text_datetime),
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        reply_markup=types.InlineKeyboardMarkup()
    )

    await bot.send_message(user.id, bot_utils.TEXT['menu'], reply_markup=bot_utils.keyboard_start)

    await bot.send_audio(ADMINS_CHAT_ID, query.message.audio.file_id, text_admin,
                         reply_markup=admin_keyboard)


async def admin_cancel(query, day: int, time: int, status: bool):
    user = query.message.caption_entities[0].user
    name = bot_utils.get_audio_name(query.message.audio)

    admin_keyboard = bot_utils.keyboard_admin(day, time, name, user.id)
    now = bot_utils.is_break_now(day, time)
    text_datetime = bot_utils.TEXT['days1'][day] + ', ' + bot_utils.get_break_name(time)
    text_admin = ('‼️' if now else '❗️') + \
                 'Новый заказ - ' + text_datetime + \
                 (' (сейчас!)' if now else '') + \
                 ' от ' + bot_utils.get_user_name(user)

    await bot.edit_message_caption(caption=text_admin, chat_id=ADMINS_CHAT_ID,
                                   message_id=query.message.message_id,
                                   reply_markup=admin_keyboard)

    if status:
        path = bot_utils.get_music_path(day, time) / (name + '.mp3')

        for i in music_api.radioboss_api(action='getplaylist2'):  # удалить из плейлиста радиобосса
            if i.attrib['FILENAME'] == str(path):
                music_api.radioboss_api(action='delete', pos=i.attrib['INDEX'])
                break
        bot_utils.delete_file(path)  # удалить с диска


async def admin_check_text(query):
    name = bot_utils.get_audio_name(query.message.audio)
    text = music_api.search_text(name)
    bad_words = bot_utils.check_bad_words(text)
    await bot.answer_callback_query(query.id, text=bad_words)


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
        await query.message.audio.download(to, timeout=60)
        bot_utils.write_sender_tag(to, query.message.caption_entities[0].user)

        if day == datetime.today().weekday() and time == bot_utils.get_break_num():
            music_api.radioboss_api(action='inserttrack', filename=to, pos=-2)
            await bot.send_message(user_id, bot_utils.TEXT['predlozka_ok_next'].format(name))
        else:
            await bot.send_message(user_id, bot_utils.TEXT['predlozka_ok'].format(name))
    else:
        await bot.send_message(user_id, bot_utils.TEXT['predlozka_neok'].format(name))


async def predlozka_day_back(query):
    await bot.edit_message_caption(
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        caption='Выбери день', reply_markup=bot_utils.keyboard_day()
    )


async def predlozka_cancel(query):
    await bot.edit_message_caption(
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        caption='Ну ок(', reply_markup=types.InlineKeyboardMarkup()
    )
    await bot.send_message(query.message.chat.id, bot_utils.TEXT['menu'], reply_markup=bot_utils.keyboard_start)


async def song_prev(query):
    playback = playlist_api.prev_get()
    if not playback:
        return await bot.send_message(query.message.chat.id, bot_utils.TEXT['song_no_prev'],
                                      reply_markup=bot_utils.keyboard_start)

    text = song_format(playback)
    await bot.send_message(query.message.chat.id, text)


async def song_next(query):
    playback = playlist_api.next_get()
    if not playback:
        return await bot.send_message(query.message.chat.id, bot_utils.TEXT['song_no_next'],
                                      reply_markup=bot_utils.keyboard_start)

    text = song_format(playback)
    await bot.send_message(query.message.chat.id, text)


def song_format(playback):
    text = [
        f"🕖<b>{track['time_start']}</b> {track['title']}"
        for track in playback
    ]
    return '\n'.join(text)


async def admin_reply(message):
    if message.reply_to_message.audio:  # на заказ
        to = message.reply_to_message.caption_entities[0].user.id
        txt = "На ваш заказ <i>(" + bot_utils.get_audio_name(
            message.reply_to_message.audio) + ")</i> ответили:"

    if message.reply_to_message.forward_from:  # на отзыв
        to = message.reply_to_message.forward_from.id
        txt = "  На ваше сообщение ответили: "

    await bot.send_message(to, txt)
    if message.audio:
        await bot.send_audio(to, message.audio.file_id)
    elif message.sticker:
        await bot.send_sticker(to, message.sticker.file_id)
    elif message.photo:
        await bot.send_photo(to, message.photo.file_id)
    else:
        await bot.send_message(to, message.text, parse_mode='markdown')


async def search_audio(message):
    await bot.send_chat_action(message.chat.id, 'upload_audio')
    audio = music_api.search(message.text)

    if not audio:
        await bot.send_message(message.chat.id, 'Ничего не нашел( \n'
                                                'Можешь загрузить свое аудио сам или переслать от другого бота!',
                               reply_markup=bot_utils.keyboard_start)
    else:
        audio = audio[0]
        try:
            # скачивание файла шоб поставить норм имя песне
            audio_file = music_api.download(audio['url'])

            # это почему то не работает
            # url = 'http://svinua.cf/api/music/?name={}&download={}'.format(
            #    urllib.parse.quote_plus(audio['artist'] + ' - ' + audio['title']), audio['url']
            # )

            await bot.send_audio(
                message.chat.id, audio_file,
                'Выбери день (или отредактируй название)',
                performer=audio['artist'],
                title=audio['title'],
                reply_markup=bot_utils.keyboard_day()
            )

        except Exception as ex:
            logging.error(f'send audio: {ex} {audio["url"]}')
            await bot.send_message(message.chat.id, bot_utils.TEXT['error'],
                                   reply_markup=bot_utils.keyboard_start)


async def inline_search(inline_query):
    name = inline_query.query
    music = music_api.search(name)
    if not music:
        return await bot.answer_inline_query(inline_query.id, [])

    articles = []
    for i in range(min(50, len(music))):
        audio = music[i]
        if not audio or not audio['url']:
            continue
        url = 'http://svinua.cf/api/music/?name={}&download={}'.format(
            urllib.parse.quote_plus(audio['artist'] + ' - ' + audio['title']), audio['url']
        )
        articles.append(
            types.InlineQueryResultAudio(
                id=str(i),
                audio_url=url,
                performer=audio['artist'],
                title=audio['title']
            )
        )
    await bot.answer_inline_query(inline_query.id, articles)


async def admin_ban(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return
    if message.reply_to_message is None:
        await bot.send_message(message.chat.id, "Перешлите сообщение пользователя, которого нужно забанить")
        return

    cmd = message.text.split(' ')
    user = message.reply_to_message.caption_entities[0].user if message.reply_to_message.audio else \
        message.reply_to_message.forward_from
    ban_time = int(cmd[1]) if len(cmd) >= 2 else \
        60 * 24
    reason = " Причина: " + ' '.join(cmd[2:]) if len(cmd) >= 3 else ""
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

    sender_name = bot_utils.read_sender_tag(fields['path'])
    sender_name = 'Заказал(а) ' + sender_name if sender_name else \
                  'От команды РадиоКпи'

    f = open(fields['path'], 'rb')
    await bot.send_audio(HISTORY_CHAT_ID, f, sender_name,
                         performer=fields['artist'], title=fields['title'])
    f.close()


def send_live_begin(time):
    async def send():
        await bot.send_message(HISTORY_CHAT_ID, bot_utils.get_break_name(time))

    asyncio.ensure_future(send())
