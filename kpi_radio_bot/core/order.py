from datetime import datetime

from aiogram import types

import keyboards
from config import bot, ADMINS_CHAT_ID
from consts import TextConstants, TIMES_NAME
from utils import other, radioboss, files, db, stats
from . import communication, users


async def order_day_choiced(query, day: int):
    is_moder = await other.is_moder(query.from_user.id)
    await bot.edit_message_caption(
        query.message.chat.id, query.message.message_id,
        caption=TextConstants.ORDER_CHOOSE_TIME.format(TIMES_NAME['week_days'][day]),
        reply_markup=await keyboards.choice_time(day, 0 if is_moder else 5)
    )


async def order_time_choiced(query, day: int, time: int):
    user = query.from_user

    is_ban = await db.ban_get(user.id)
    if is_ban:
        return await bot.send_message(query.message.chat.id, TextConstants.BAN_TRY_ORDER.format(
                                      datetime.fromtimestamp(is_ban).strftime("%d.%m %H:%M")))

    admin_text, also = await other.gen_order_caption(day, time, user,
                                                     audio_name=other.get_audio_name(query.message.audio))

    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=TextConstants.ORDER_ON_MODERATION.format(also['text_datetime']),
                                   reply_markup=types.InlineKeyboardMarkup())
    await users.menu(query.message)

    m = await bot.send_audio(ADMINS_CHAT_ID, query.message.audio.file_id, admin_text,
                             reply_markup=keyboards.admin_choose(day, time))
    communication.cache_add(m.message_id, query.message)
    communication.cache_add(query.message.message_id, m)


async def order_day_unchoiced(query):
    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=TextConstants.ORDER_CHOOSE_DAY, reply_markup=await keyboards.choice_day())


async def order_cancel(query):
    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=TextConstants.ORDER_CANCELED, reply_markup=types.InlineKeyboardMarkup())
    await users.menu(query.message)


async def admin_choice(query, day: int, time: int, status: str):
    audio_name = other.get_audio_name(query.message.audio)
    user = other.get_user_from_entity(query.message)

    admin_text, also = await other.gen_order_caption(day, time, user, status=status, moder=query.from_user)
    await bot.edit_message_caption(query.message.chat.id, query.message.message_id, caption=admin_text,
                                   reply_markup=keyboards.admin_unchoose(day, time, status))

    stats.add(audio_name, query.from_user.id, user.id, status, str(datetime.now()), query.message.message_id)

    if status == 'reject':  # кнопка отмена
        m = await bot.send_message(user.id, TextConstants.ORDER_ERR_DENIED.format(audio_name, also['text_datetime']))
        return communication.cache_add(m.message_id, query.message)

    path = other.get_audio_path(day, time, audio_name)
    await files.download_audio(query.message.audio, path)
    await radioboss.write_track_additional_info(path, user, query.message.message_id)

    if status == 'now':  # кнопка сейчас
        when_playing = 'прямо сейчас!'
        await radioboss.radioboss_api(action='inserttrack', filename=path, pos=-2)
        m = await bot.send_message(user.id, TextConstants.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))
        communication.cache_add(m.message_id, query.message)

    if status == 'queue':  # кнопка принять

        if not also['now']:  # если щас не этот эфир то похуй
            when_playing = 'Заиграет когда надо'
            m = await bot.send_message(user.id, TextConstants.ORDER_ACCEPTED.format(audio_name, also['text_datetime']))
            communication.cache_add(m.message_id, query.message)
        elif await radioboss.find_in_playlist_by_path(str(path)):
            when_playing = 'Такой же трек уже принят на этот эфир'
            m = await bot.send_message(user.id, TextConstants.ORDER_ACCEPTED.format(audio_name, also['text_datetime']))
            communication.cache_add(m.message_id, query.message)
        else:
            last_track = await radioboss.get_new_order_pos()
            if not last_track:  # нету места
                when_playing = 'не успел :('
                m = await bot.send_audio(user.id, query.message.audio.file_id, reply_markup=await keyboards.choice_day(),
                                         caption=TextConstants.ORDER_ERR_ACCEPTED_TOOLATE.
                                         format(audio_name, also['text_datetime']))
                communication.cache_add(m.message_id, query.message)

            else:  # есть место
                minutes_left = round((last_track['time_start'] - datetime.now()).seconds / 60)
                when_playing = f'через {minutes_left} ' + other.case_by_num(minutes_left, 'минуту', 'минуты', 'минут')

                await radioboss.radioboss_api(action='inserttrack', filename=path, pos=last_track['index'])
                m = await bot.send_message(user.id, TextConstants.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))
                communication.cache_add(m.message_id, query.message)

    await bot.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=admin_text + '\n🕑 ' + when_playing,
                                   reply_markup=keyboards.admin_unchoose(day, time, status))


async def admin_unchoice(query, day: int, time: int, status: str):
    user = other.get_user_from_entity(query.message)
    audio_name = other.get_audio_name(query.message.audio)
    admin_text, _ = await other.gen_order_caption(day, time, user, audio_name=other.get_audio_name(query.message.audio))
    await bot.edit_message_caption(ADMINS_CHAT_ID, query.message.message_id,
                                   caption=admin_text, reply_markup=keyboards.admin_choose(day, time))

    if status != 'reject':  # если заказ был принят а щас отменяют
        path = other.get_audio_path(day, time, audio_name)
        files.delete_file(path)  # удалить с диска
        for i in await radioboss.find_in_playlist_by_path(str(path)):
            await radioboss.radioboss_api(action='delete', pos=i['index'])
