import logging
import asyncio
from datetime import datetime

from aiogram import types

import consts
import keyboards
from config import *
from utils import other, radioboss, music, broadcast, files, db


# key value db: admins_message_id: (user_id, user_message_id)
USER2ADMINS_MESSAGES = {}


def add_to_user2admins(admin_msg, user_id, user_msg):
    USER2ADMINS_MESSAGES[admin_msg] = (user_id, user_msg)
    while len(USER2ADMINS_MESSAGES) > 500:
        del USER2ADMINS_MESSAGES[list(USER2ADMINS_MESSAGES.keys())[0]]


async def order_day_choiced(query, day: int):
    await bot.edit_message_caption(
        query.message.chat.id, query.message.message_id,
        caption=consts.TextConstants.ORDER_CHOOSE_TIME.format(consts.times_name['week_days'][day]),
        reply_markup=await keyboards.choice_time(day)
    )


async def order_time_choiced(query, day: int, time: int):
    user = query.from_user

    is_ban = db.ban_get(user.id)
    if is_ban:
        return await bot.send_message(query.message.chat.id, "Вы не можете предлагать музыку до " +
                                      datetime.fromtimestamp(is_ban).strftime("%d.%m %H:%M"))

    admin_text, also = await other.gen_order_caption(day, time, user,
                                                     audio_name=other.get_audio_name(query.message.audio))

    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=consts.TextConstants.ORDER_ON_MODERATION.format(also['text_datetime']),
                                   reply_markup=types.InlineKeyboardMarkup())
    await bot.send_message(query.message.chat.id, consts.TextConstants.MENU, reply_markup=keyboards.start)
    admin_message = await bot.send_audio(ADMINS_CHAT_ID, query.message.audio.file_id, admin_text,
                                         reply_markup=keyboards.admin_choose(day, time))
    add_to_user2admins(admin_message.message_id, query.message.chat.id, query.message.message_id)


async def order_day_unchoiced(query):
    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=consts.TextConstants.ORDER_CHOOSE_DAY,
                                   reply_markup=await keyboards.choice_day())


async def order_cancel(query):
    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=consts.TextConstants.ORDER_CANCELED,
                                   reply_markup=types.InlineKeyboardMarkup())
    await bot.send_message(query.message.chat.id, consts.TextConstants.MENU, reply_markup=keyboards.start)


async def admin_choice(query, day: int, time: int, status: str):
    audio_name = other.get_audio_name(query.message.audio)
    user = query.message.caption_entities[0].user

    admin_text, also = await other.gen_order_caption(day, time, user, status=status, moder=query.from_user)
    await bot.edit_message_caption(query.message.chat.id, query.message.message_id, caption=admin_text,
                                   reply_markup=keyboards.admin_unchoose(day, time, status))

    other.add_moder_stats(audio_name, query.from_user.username, user.username, status, str(datetime.now()))

    if status == 'reject':  # отмена
        return await bot.send_message(user.id,
                                      consts.TextConstants.ORDER_ERR_DENIED.format(audio_name, also['text_datetime']))

    to = broadcast.get_broadcast_path(day, time) / (audio_name + '.mp3')
    files.create_dirs(to)
    await query.message.audio.download(to, timeout=60)
    await radioboss.write_track_additional_info(to, user, query.message.message_id)

    if not also['now']:  # если щас не этот эфир то похуй
        return await bot.send_message(user.id,
                                      consts.TextConstants.ORDER_ACCEPTED.format(audio_name, also['text_datetime']))

    # todo check doubles

    when_playing = ''
    if status == 'now':  # следующим
        when_playing = 'прямо сейчас!'
        await radioboss.radioboss_api(action='inserttrack', filename=to, pos=-2)
        await bot.send_message(user.id, consts.TextConstants.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))

    if status == 'queue':  # в очередь
        last_track = await radioboss.get_new_order_pos()
        if not last_track:  # нету места
            when_playing = 'не успел :('
            await bot.send_message(user.id,
                                   consts.TextConstants.ORDER_ERR_TOOLATE.format(audio_name, also['text_datetime']))
        else:  # есть место
            minutes_left = round((last_track['time_start'] - datetime.now()).seconds / 60)
            when_playing = f'через {minutes_left} ' + other.case_by_num(minutes_left, 'минуту', 'минуты', 'минут')

            await radioboss.radioboss_api(action='inserttrack', filename=to, pos=last_track['index'])
            await bot.send_message(user.id, consts.TextConstants.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))

    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=admin_text + '\n🕑 ' + when_playing,
                                   reply_markup=keyboards.admin_unchoose(day, time, status))


async def admin_unchoice(query, day: int, time: int, status: str):
    user = query.message.caption_entities[0].user
    name = other.get_audio_name(query.message.audio)

    admin_text, _ = await other.gen_order_caption(day, time, user,
                                                  audio_name=other.get_audio_name(query.message.audio))

    await bot.edit_message_caption(ADMINS_CHAT_ID, query.message.message_id,
                                   caption=admin_text, reply_markup=keyboards.admin_choose(day, time))

    if status != 'reject':  # если заказ был принят а щас отменяют
        path = broadcast.get_broadcast_path(day, time) / (name + '.mp3')
        files.delete_file(path)  # удалить с диска
        for i in await radioboss.radioboss_api(action='getplaylist2'):  # удалить из плейлиста радиобосса
            if i.attrib['FILENAME'] == str(path):
                await radioboss.radioboss_api(action='delete', pos=i.attrib['INDEX'])
                break


async def admin_reply(message):
    if message.text and message.text.startswith("!"):  # игнор ответа
        return

    if message.reply_to_message.message_id in USER2ADMINS_MESSAGES:
        user, reply_to = USER2ADMINS_MESSAGES[message.reply_to_message.message_id]
    else:
        if message.reply_to_message.audio:  # на заказ
            user = message.reply_to_message.caption_entities[0].user.id
            txt = "На ваш заказ <i>(" + other.get_audio_name(message.reply_to_message.audio) + ")</i> ответили:"
        elif message.reply_to_message.forward_from:  # на отзыв
            user = message.reply_to_message.forward_from.id
            txt = "На ваше сообщение ответили: "
        else:
            return
        reply_to = None
        await bot.send_message(user, txt)

    if message.audio:
        await bot.send_audio(user, message.audio.file_id, reply_to_message_id=reply_to)
    elif message.sticker:
        await bot.send_sticker(user, message.sticker.file_id, reply_to_message_id=reply_to)
    elif message.photo:
        await bot.send_photo(user, message.photo[-1].file_id, reply_to_message_id=reply_to, caption=message.caption)
    else:
        await bot.send_message(user, message.text, reply_to_message_id=reply_to, parse_mode='markdown')


async def admin_ban(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return
    if message.reply_to_message is None:
        return await bot.send_message(message.chat.id, "Перешлите сообщение пользователя, которого нужно забанить")

    cmd = message.get_args().split(' ', 1)
    user = message.reply_to_message.caption_entities[0].user \
        if message.reply_to_message.audio else message.reply_to_message.forward_from
    ban_time = int(cmd[0]) if cmd[0].isdigit() else 60 * 24
    reason = f" Бан по причине: <i>{cmd[1]}</i>" if len(cmd) >= 2 else ""
    db.ban_set(user.id, ban_time)

    if ban_time == 0:
        return await bot.send_message(message.chat.id, f"{other.get_user_name(user)} разбанен")
    await bot.send_message(message.chat.id, f"{other.get_user_name(user)} забанен на {ban_time} минут. {reason}")
    await bot.send_message(user.id, f"Вы были забанены на {ban_time} минут. {reason}")


async def admin_set_volume(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return

    if not broadcast.is_broadcast_right_now():
        await message.reply(text="Богдан пошел нахуй" if message.from_user.id == 337283845 else "Только во время эфира")

    cmd = message.get_args().split()
    if message.get_args().isdigit():
        volume = int(message.get_args())
        if 0 < volume < 100:
            await radioboss.radioboss_api(cmd=f'setvol {volume}')
            return await message.reply(text=f'Громкость выставлена в {volume}!')

    await message.reply(text=f'Головонька опухла! Громкость - число от 0 до 100, а не <code>{cmd[0]}</code>')


async def admin_stats(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return

    if 'csv' in message.get_args():
        with open(PATH_STUFF / 'stats.csv', 'rb') as file:
            await bot.send_document(message.chat.id, file)
    else:
        days = int(message.get_args()) if message.get_args().isdigit() else 7
        other.gen_stats_graph(days)
        with open(PATH_STUFF / 'stats.png', 'rb') as file:
            await bot.send_photo(message.chat.id, file, caption=f'Стата за {days} дн.')


async def song_now(message):
    playback = await radioboss.get_now()
    if not playback:
        return await bot.send_message(message.chat.id, "Не знаю(", reply_markup=keyboards.what_playing)
    await bot.send_message(message.chat.id, consts.TextConstants.WHAT_PLAYING.format(*playback),
                           reply_markup=keyboards.what_playing)


async def song_prev(query):
    playback = await radioboss.get_prev()
    if not playback:
        return await bot.send_message(query.message.chat.id, consts.TextConstants.SONG_NO_PREV)
    await bot.send_message(query.message.chat.id, other.song_format(playback))


async def song_next(query):
    playback = await radioboss.get_next()
    if not playback:
        return await bot.send_message(query.message.chat.id, consts.TextConstants.SONG_NO_NEXT)
    await bot.send_message(query.message.chat.id, other.song_format(playback[:5]))


async def timetable(message):
    t = ''
    for day_num, day_name in {0: 'Будни', 6: 'Воскресенье'}.items():
        t += f"{day_name} \n"
        for break_num, (start, stop) in consts.broadcast_times[day_num].items():
            t += f"   {start} - {stop}   {broadcast.get_broadcast_name(break_num)} \n"

    # todo
    # t += "До ближайшего эфира ..."

    await bot.send_message(message.chat.id, t)


async def help_change(query, key):
    try:
        await bot.edit_message_text(getattr(consts.HelpConstants, key.upper()), query.message.chat.id,
                                    query.message.message_id, reply_markup=keyboards.choice_help)
    except:
        pass


async def feedback(message):
    admin_message = await bot.forward_message(ADMINS_CHAT_ID, message.chat.id, message.message_id)
    add_to_user2admins(admin_message.message_id, message.chat.id, message.message_id)


async def search_audio(message):
    await bot.send_chat_action(message.chat.id, 'upload_audio')
    audio = await music.search(message.text)

    if not audio:
        return await bot.send_message(message.chat.id, consts.TextConstants.SEARCH_FAILED, reply_markup=keyboards.start)

    audio = audio[0]
    try:
        await bot.send_audio(
            message.chat.id,
            music.get_download_url(audio['url'], audio['artist'], audio['title']),
            consts.TextConstants.ORDER_CHOOSE_DAY, reply_markup=await keyboards.choice_day()
        )
    except Exception as ex:
        logging.error(f'send audio: {ex} {audio["url"]}')
        await bot.send_message(message.chat.id, consts.TextConstants.ERROR, reply_markup=keyboards.start)


async def inline_search(inline_query):
    name = inline_query.query
    audios = await music.search(name)
    if not audios:
        return await bot.answer_inline_query(inline_query.id, [])

    articles = []
    for i in range(min(50, len(audios))):
        audio = audios[i]
        if not audio or not audio['url']:
            continue
        articles.append(types.InlineQueryResultAudio(
            id=str(hash(audio['url'])),
            audio_url=music.get_download_url(audio['url'], audio['artist'], audio['title']),
            performer=audio['artist'],
            title=audio['title']
        ))
    await bot.answer_inline_query(inline_query.id, articles)


async def send_history(fields):
    if str(consts.paths['archive']) in fields['path']:  # песни с архива не играют на политехнической, только на ютубе
        return

    if not fields['artist'] and not fields['title']:
        fields['title'] = fields['casttitle']

    sender_name = ''
    tag = await radioboss.read_track_additional_info(fields['path'])
    await radioboss.clear_track_additional_info(fields['path'])  # Очистить тег что бы уведомление не пришло еще раз

    if tag:
        sender_name = consts.TextConstants.HISTORY_TITLE.format(other.get_user_name_(tag['id'], tag['name']))
        if not db.notification_get(tag['id']):
            await bot.send_message(tag['id'], consts.TextConstants.ORDER_PLAYING.format(fields['casttitle']))
        await bot.edit_message_reply_markup(ADMINS_CHAT_ID, tag['moderation_id'], reply_markup=None)

    with open(fields['path'], 'rb') as f:
        await bot.send_audio(HISTORY_CHAT_ID, f, sender_name, performer=fields['artist'], title=fields['title'])


async def broadcast_begin(time):
    await bot.send_message(HISTORY_CHAT_ID, broadcast.get_broadcast_name(time))


async def broadcast_end(day, time):
    files = broadcast.get_broadcast_path(day, time).iterdir()
    for file_path in files:
        tag = await radioboss.read_track_additional_info(file_path)
        if not tag:
            continue
        with open(str(file_path), 'rb') as file:
            await bot.send_audio(tag['id'], file, caption=consts.TextConstants.ORDER_PEREZAKLAD,
                                 reply_markup=await keyboards.choice_day())
        await asyncio.sleep(3)

