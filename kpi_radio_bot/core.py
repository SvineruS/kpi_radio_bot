import logging
from datetime import datetime

from aiogram import types

import ban
import bot_utils
import consts
import keyboards
import music_api
import playlist_api
from config import *


async def order_day_choiced(query, day: int):
    await bot.edit_message_caption(
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        caption=consts.text['order_choose_time'].format(consts.times_name['week_days'][day]),
        reply_markup=await keyboards.choice_time(day)
    )


async def order_time_choiced(query, day: int, time: int):
    user = query.from_user
    name = bot_utils.get_audio_name(query.message.audio)

    is_ban = ban.chek_ban(user.id)
    if is_ban:
        return await bot.send_message(query.message.chat.id, "Вы не можете предлагать музыку до " +
                                      datetime.fromtimestamp(is_ban).strftime("%d.%m %H:%M"))

    admin_keyboard = keyboards.admin_choose(day, time, name, user.id)
    now = bot_utils.is_break_now(day, time)
    text_datetime = consts.times_name['week_days'][day] + ', ' + bot_utils.get_break_name(time)
    text_admin = ('‼️' if now else '❗️') + \
                 'Новый заказ - ' + text_datetime + \
                 (' (сейчас!)' if now else '') + \
                 ' от ' + bot_utils.get_user_name(user)

    await bot.edit_message_caption(
        caption=consts.text['order_moderating'].format(text_datetime),
        chat_id=query.message.chat.id,
        message_id=query.message.message_id,
        reply_markup=types.InlineKeyboardMarkup()
    )

    await bot.send_message(user.id, consts.text['menu'], reply_markup=keyboards.start)

    await bot.send_audio(ADMINS_CHAT_ID, query.message.audio.file_id, text_admin,
                         reply_markup=admin_keyboard)


async def oder_day_unchoiced(query):
    await bot.edit_message_caption(
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        caption='Выбери день', reply_markup=await keyboards.choice_day()
    )


async def order_cancel(query):
    await bot.edit_message_caption(
        chat_id=query.message.chat.id, message_id=query.message.message_id,
        caption='Ну ок(', reply_markup=types.InlineKeyboardMarkup()
    )
    await bot.send_message(query.message.chat.id, consts.text['menu'], reply_markup=keyboards.start)


async def admin_choice(query, status: str, user_id, day: int, time: int):
    name = bot_utils.get_audio_name(query.message.audio)

    new_text = 'Заказ: ' + query.message.caption.split(' - ')[1].split(' от')[0] + \
               ', от ' + bot_utils.get_user_name(query.message.caption_entities[0].user) + \
               ' - ' + ("✅Принят" if status else "❌Отклонен") + \
               ' (' + bot_utils.get_user_name(query.from_user) + ')'

    keyboard_cancel = keyboards.admin_unchoose(day, time, status != 'reject')

    await bot.edit_message_caption(caption=new_text,
                                   chat_id=query.message.chat.id, message_id=query.message.message_id,
                                   reply_markup=keyboard_cancel
                                   )

    if status == 'reject':                       # отмена
        return await bot.send_message(user_id, consts.text['order_neok'].format(name))

    to = bot_utils.get_music_path(day, time) / (name + '.mp3')
    bot_utils.create_dirs(to)
    await query.message.audio.download(to, timeout=60)
    await bot_utils.write_sender_tag(to, query.message.caption_entities[0].user)

    if not bot_utils.is_break_now(day, time):    # если щас не жфир то похуй
        return await bot.send_message(user_id, consts.text['order_ok'].format(name))

    if status == 'now':                          # поставить следующим
        await music_api.radioboss_api(action='inserttrack', filename=to, pos=-2)
        await bot.send_message(user_id, consts.text['order_ok_next'].format(name, 'прямо сейчас'))

    if status == 'queue':                        # поставить в очередь
        last_track = await playlist_api.get_new_order_pos()
        if not last_track:
            return  # todo "ваш трек неуспел :("
        minutes_left = round((last_track['time_start'] - datetime.now().time()).seconds / 60)
        minutes_left = str(minutes_left) + bot_utils.case_by_num(minutes_left, 'минуту', 'минуты', 'минут')
        await music_api.radioboss_api(action='inserttrack', filename=to, pos=last_track['index'])
        await bot.send_message(user_id, consts.text['order_ok_next'].format(name, minutes_left))


async def admin_unchoice(query, day: int, time: int, status: str):
    user = query.message.caption_entities[0].user
    name = bot_utils.get_audio_name(query.message.audio)

    admin_keyboard = keyboards.admin_choose(day, time, name, user.id)
    now = bot_utils.is_break_now(day, time)
    text_datetime = consts.times_name['week_days'][day] + ', ' + bot_utils.get_break_name(time)
    text_admin = ('‼️' if now else '❗️') + \
                 'Новый заказ - ' + text_datetime + \
                 (' (сейчас!)' if now else '') + \
                 ' от ' + bot_utils.get_user_name(user)

    await bot.edit_message_caption(caption=text_admin, chat_id=ADMINS_CHAT_ID,
                                   message_id=query.message.message_id,
                                   reply_markup=admin_keyboard)

    if status != 'reject':
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


async def admin_reply(message):
    if message.text and message.text.startswith("!"):  # игнор ответа
        return

    to = txt = None
    if message.reply_to_message.audio:         # на заказ
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


async def admin_ban(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return
    if message.reply_to_message is None:
        return await bot.send_message(message.chat.id, "Перешлите сообщение пользователя, которого нужно забанить")

    cmd = message.get_args()
    user = message.reply_to.caption_entities[0].user if message.reply_to.audio else message.reply_to.forward_from
    ban_time = int(cmd[1]) if len(cmd) >= 1 else 60 * 24
    reason = (" Бан по причине: <i>" + ' '.join(cmd[2:]) + "</i>") if len(cmd) >= 2 else ""
    ban.ban_user(user.id, ban_time)

    if ban_time == 0:
        return await bot.send_message(message.chat.id, f"{bot_utils.get_user_name(user)} разбанен")
    await bot.send_message(message.chat.id, f"{bot_utils.get_user_name(user)} забанен на {ban_time} минут. {reason}")
    await bot.send_message(user.id, f"Вы были забанены на {ban_time} минут. {reason}")


async def song_now(message):
    playback = await playlist_api.get_now()
    if not playback:
        return await bot.send_message(message.chat.id, "Не знаю(", reply_markup=keyboards.what_playing)
    await bot.send_message(message.chat.id, consts.text['what_playing'].format(*playback),
                           reply_markup=keyboards.what_playing)


async def song_prev(query):
    playback = await playlist_api.get_prev()
    if not playback:
        return await bot.send_message(query.message.chat.id, consts.text['song_no_prev'])
    await bot.send_message(query.message.chat.id, bot_utils.song_format(playback))


async def song_next(query):
    playback = await playlist_api.get_next()
    if not playback:
        return await bot.send_message(query.message.chat.id, consts.text['song_no_next'])
    await bot.send_message(query.message.chat.id, bot_utils.song_format(playback[:5]))


async def help_change(query, key):
    try:
        await bot.edit_message_text(consts.help[key], query.message.chat.id, query.message.message_id,
                                    reply_markup=keyboards.choice_help)
    except:
        pass


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
                reply_markup=await keyboards.choice_day()
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
        articles.append(types.InlineQueryResultAudio(
            id=str(hash(audio['url'])),
            audio_url=music_api.get_download_url(audio['url'], audio['artist'], audio['title']),
            performer=audio['artist'],
            title=audio['title']
        ))
    await bot.answer_inline_query(inline_query.id, articles)


async def send_history(fields):
    if not fields['artist'] and not fields['title']:
        fields['title'] = fields['casttitle']

    sender_name = await bot_utils.read_sender_tag(fields['path'])
    sender_name = 'Заказал(а) ' + sender_name if sender_name else 'От команды РадиоКпи'

    f = open(fields['path'], 'rb')
    await bot.send_audio(HISTORY_CHAT_ID, f, sender_name, performer=fields['artist'], title=fields['title'])
    f.close()


async def send_live_begin(time):
    await bot.send_message(HISTORY_CHAT_ID, bot_utils.get_break_name(time))
