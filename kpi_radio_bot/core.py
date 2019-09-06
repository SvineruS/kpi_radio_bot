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
        query.message.chat.id, query.message.message_id,
        caption=consts.TextConstants.ORDER_CHOOSE_TIME.format(consts.times_name['week_days'][day]),
        reply_markup=await keyboards.choice_time(day)
    )


async def order_time_choiced(query, day: int, time: int):
    user = query.from_user

    is_ban = ban.check_ban(user.id)
    if is_ban:
        return await bot.send_message(query.message.chat.id, "Вы не можете предлагать музыку до " +
                                      datetime.fromtimestamp(is_ban).strftime("%d.%m %H:%M"))

    admin_text, also = await bot_utils.gen_order_caption(day, time, user,
                                                         audio_name=bot_utils.get_audio_name(query.message.audio))

    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=consts.TextConstants.ORDER_ON_MODERATION.format(also['text_datetime']),
                                   reply_markup=types.InlineKeyboardMarkup())
    await bot.send_message(query.message.chat.id, consts.TextConstants.MENU, reply_markup=keyboards.start)
    await bot.send_audio(ADMINS_CHAT_ID, query.message.audio.file_id, admin_text,
                         reply_markup=keyboards.admin_choose(day, time))
    

async def order_day_unchoiced(query):
    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=consts.TextConstants.ORDER_CHOOSE_DAY, reply_markup=await keyboards.choice_day())


async def order_cancel(query):
    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=consts.TextConstants.ORDER_CANCELED, reply_markup=types.InlineKeyboardMarkup())
    await bot.send_message(query.message.chat.id, consts.TextConstants.MENU, reply_markup=keyboards.start)


async def admin_choice(query, day: int, time: int, status: str):
    audio_name = bot_utils.get_audio_name(query.message.audio)
    user = query.message.caption_entities[0].user

    admin_text, also = await bot_utils.gen_order_caption(day, time, user, status=status, moder=query.from_user)
    await bot.edit_message_caption(query.message.chat.id, query.message.message_id, caption=admin_text,
                                   reply_markup=keyboards.admin_unchoose(day, time, status))

    bot_utils.add_moder_stats(audio_name, query.from_user.username, user.username, status, str(datetime.now()))

    if status == 'reject':  # отмена
        return await bot.send_message(user.id, consts.TextConstants.ORDER_ERR_DENIED.format(audio_name))

    to = bot_utils.get_music_path(day, time) / (audio_name + '.mp3')
    bot_utils.create_dirs(to)
    await query.message.audio.download(to, timeout=60)
    await bot_utils.write_sender_tag(to, user, query.message.message_id)

    if not also['now']:  # если щас не этот эфир то похуй
        return await bot.send_message(user.id, consts.TextConstants.ORDER_ACCEPTED.format(audio_name))

    # todo check doubles

    when_playing = ''
    if status == 'now':  # следующим
        when_playing = 'прямо сейчас!'
        await music_api.radioboss_api(action='inserttrack', filename=to, pos=-2)
        await bot.send_message(user.id, consts.TextConstants.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))

    if status == 'queue':  # в очередь
        last_track = await playlist_api.get_new_order_pos()
        if not last_track:  # нету места
            when_playing = 'не успел :('
            await bot.send_message(user.id, consts.TextConstants.ORDER_ERR_TOOLATE.format(audio_name))
        else:  # есть место
            minutes_left = round((last_track['time_start'] - datetime.now()).seconds / 60)
            when_playing = f'через {minutes_left} ' + bot_utils.case_by_num(minutes_left, 'минуту', 'минуты', 'минут')

            await music_api.radioboss_api(action='inserttrack', filename=to, pos=last_track['index'])
            await bot.send_message(user.id, consts.TextConstants.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))

    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=admin_text + '\n🕑 ' + when_playing,
                                   reply_markup=keyboards.admin_unchoose(day, time, status))


async def admin_unchoice(query, day: int, time: int, status: str):
    user = query.message.caption_entities[0].user
    name = bot_utils.get_audio_name(query.message.audio)

    admin_text, _ = await bot_utils.gen_order_caption(day, time, user,
                                                      audio_name=bot_utils.get_audio_name(query.message.audio))

    await bot.edit_message_caption(ADMINS_CHAT_ID, query.message.message_id,
                                   caption=admin_text, reply_markup=keyboards.admin_choose(day, time))

    if status != 'reject':  # если заказ был принят а щас отменяют
        path = bot_utils.get_music_path(day, time) / (name + '.mp3')
        bot_utils.delete_file(path)  # удалить с диска
        for i in await music_api.radioboss_api(action='getplaylist2'):  # удалить из плейлиста радиобосса
            if i.attrib['FILENAME'] == str(path):
                await music_api.radioboss_api(action='delete', pos=i.attrib['INDEX'])
                break


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


async def admin_ban(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return
    if message.reply_to_message is None:
        return await bot.send_message(message.chat.id, "Перешлите сообщение пользователя, которого нужно забанить")

    cmd = message.get_args().split(' ', 1)
    user = message.reply_to_message.caption_entities[0].user \
        if message.reply_to_message.audio else message.reply_to_message.forward_from
    ban_time = int(cmd[0]) if len(cmd) >= 1 else 60 * 24
    reason = f" Бан по причине: <i>{cmd[1]}</i>" if len(cmd) >= 2 else ""
    ban.ban_user(user.id, ban_time)

    if ban_time == 0:
        return await bot.send_message(message.chat.id, f"{bot_utils.get_user_name(user)} разбанен")
    await bot.send_message(message.chat.id, f"{bot_utils.get_user_name(user)} забанен на {ban_time} минут. {reason}")
    await bot.send_message(user.id, f"Вы были забанены на {ban_time} минут. {reason}")


async def admin_set_volume(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return

    cmd = message.get_args().split()
    try:
        volume_percent = int(cmd[0]) if len(cmd) >= 1 else 100
        if volume_percent < 0 or volume_percent > 100:
            raise ValueError
        await music_api.radioboss_api(cmd=f'setvol {volume_percent}')
        await message.reply(text=f'Громкость выставлена в {volume_percent}!')
    except ValueError:
        await message.reply(text=f'Головонька опухла! Громкость - число от 0 до 100, а не <code>{cmd[0]}</code>')


async def song_now(message):
    playback = await playlist_api.get_now()
    if not playback:
        return await bot.send_message(message.chat.id, "Не знаю(", reply_markup=keyboards.what_playing)
    await bot.send_message(message.chat.id, consts.TextConstants.WHAT_PLAYING.format(*playback),
                           reply_markup=keyboards.what_playing)


async def song_prev(query):
    playback = await playlist_api.get_prev()
    if not playback:
        return await bot.send_message(query.message.chat.id, consts.TextConstants.SONG_NO_PREV)
    await bot.send_message(query.message.chat.id, bot_utils.song_format(playback))


async def song_next(query):
    playback = await playlist_api.get_next()
    if not playback:
        return await bot.send_message(query.message.chat.id, consts.TextConstants.SONG_NO_NEXT)
    await bot.send_message(query.message.chat.id, bot_utils.song_format(playback[:5]))


async def timetable(message):
    t = ''
    for day_num, day_name in {0: 'Будни', 6: 'Воскресенье'}.items():
        t += f"{day_name} \n"
        for break_num, (start, stop) in consts.broadcast_times[day_num].items():
            t += f"   {start} - {stop}   {bot_utils.get_break_name(break_num)} \n"

    # todo
    # t += "До ближайшего эфира ..."

    await bot.send_message(message.chat.id, t)


async def help_change(query, key):
    try:
        await bot.edit_message_text(getattr(consts.HelpConstants, key.upper()), query.message.chat.id,
                                    query.message.message_id, reply_markup=keyboards.choice_help)
    except:
        pass


async def search_audio(message):
    await bot.send_chat_action(message.chat.id, 'upload_audio')
    audio = await music_api.search(message.text)

    if not audio:
        return await bot.send_message(message.chat.id, consts.TextConstants.SEARCH_FAILED, reply_markup=keyboards.start)

    audio = audio[0]
    try:
        await bot.send_audio(
            message.chat.id,
            music_api.get_download_url(audio['url'], audio['artist'], audio['title']),
            consts.TextConstants.ORDER_CHOOSE_DAY, reply_markup=await keyboards.choice_day()
        )
    except Exception as ex:
        logging.error(f'send audio: {ex} {audio["url"]}')
        await bot.send_message(message.chat.id, consts.TextConstants.ERROR, reply_markup=keyboards.start)


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

    sender_name = ''
    tag = await bot_utils.read_sender_tag(fields['path'])
    await playlist_api.write_tag(fields['path'], '')  # Очистить тег что бы уведомление не пришло еще раз

    if tag:
        sender_name = consts.TextConstants.HISTORY_TITLE.format(bot_utils.get_user_name_(tag['id'], tag['name']))
        if True:  # todo проверить настройки уведомлений этого юзера
            await bot.send_message(tag['id'], consts.TextConstants.ORDER_PLAYING.format(f"{fields['artist']} - {fields['title']}"))
        await bot.edit_message_reply_markup(ADMINS_CHAT_ID, tag['moderation_id'], reply_markup=None)

    with open(fields['path'], 'rb') as f:
        await bot.send_audio(HISTORY_CHAT_ID, f, sender_name, performer=fields['artist'], title=fields['title'])


async def send_live_begin(time):
    await bot.send_message(HISTORY_CHAT_ID, bot_utils.get_break_name(time))
