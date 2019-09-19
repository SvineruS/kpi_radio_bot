from datetime import datetime

from aiogram import types

import consts
import keyboards
from config import *
from utils import other, radioboss, broadcast, files, db
from . import communication


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
    communication.cache_add(admin_message.message_id, query.message)
    communication.cache_add(query.message.message_id, admin_message)


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
        m = await bot.send_message(user.id,
                                   consts.TextConstants.ORDER_ERR_DENIED.format(audio_name, also['text_datetime']))
        communication.cache_add(m, query.message)
        return

    to = broadcast.get_broadcast_path(day, time) / (audio_name + '.mp3')
    files.create_dirs(to)
    await query.message.audio.download(to, timeout=60)
    await radioboss.write_track_additional_info(to, user, query.message.message_id)

    if not also['now']:  # если щас не этот эфир то похуй
        m = await bot.send_message(user.id,
                                   consts.TextConstants.ORDER_ACCEPTED.format(audio_name, also['text_datetime']))
        communication.cache_add(m, query.message)
        return

    # todo check doubles

    when_playing = ''
    if status == 'now':  # следующим
        when_playing = 'прямо сейчас!'
        await radioboss.radioboss_api(action='inserttrack', filename=to, pos=-2)
        m = await bot.send_message(user.id, consts.TextConstants.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))
        communication.cache_add(m, query.message)

    if status == 'queue':  # в очередь
        last_track = await radioboss.get_new_order_pos()
        if not last_track:  # нету места
            when_playing = 'не успел :('
            m = await bot.send_message(user.id,
                                       consts.TextConstants.ORDER_ERR_TOOLATE.format(audio_name, also['text_datetime']))
            communication.cache_add(m, query.message)

        else:  # есть место
            minutes_left = round((last_track['time_start'] - datetime.now()).seconds / 60)
            when_playing = f'через {minutes_left} ' + other.case_by_num(minutes_left, 'минуту', 'минуты', 'минут')

            await radioboss.radioboss_api(action='inserttrack', filename=to, pos=last_track['index'])
            m = await bot.send_message(user.id,
                                       consts.TextConstants.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))
            communication.cache_add(m, query.message)

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
