"""Обработка заказов"""

# todo refactor this

from datetime import datetime
from urllib.parse import quote

from aiogram import types, exceptions
from aiogram.types import CallbackQuery

import broadcast
from config import BOT, ADMINS_CHAT_ID, HOST
from consts import texts, TIMES_NAME, keyboards
from core import communication, users
from utils import user_utils, files, db, stats, music, get_by


async def order_make(query: CallbackQuery, day: int, time: int):
    user = query.from_user

    if is_ban := await db.ban_get(user.id):
        return await BOT.send_message(query.message.chat.id, texts.BAN_TRY_ORDER.format(is_ban.strftime("%d.%m %H:%M")))

    admin_text, also = await _gen_order_caption(day, time, user, audio_name=get_by.get_audio_name(query.message.audio))

    try:
        await BOT.edit_message_caption(query.message.chat.id, query.message.message_id,
                                       caption=texts.ORDER_ON_MODERATION.format(also['text_datetime']),
                                       reply_markup=types.InlineKeyboardMarkup())
    except exceptions.MessageNotModified:
        pass

    await users.menu(query.message)

    # todo use ffmpeg
    mes = await BOT.send_audio(ADMINS_CHAT_ID, query.message.audio.file_id, admin_text,
                               reply_markup=keyboards.admin_choose(day, time))
    communication.cache_add(mes.message_id, query.message)
    communication.cache_add(query.message.message_id, mes)


async def order_choose_time(query: CallbackQuery, day: int):
    is_moder = await user_utils.is_admin(query.from_user.id)
    await BOT.edit_message_caption(
        query.message.chat.id, query.message.message_id,
        caption=texts.CHOOSE_TIME.format(TIMES_NAME['week_days'][day]),
        reply_markup=await keyboards.order_choice_time(day, 0 if is_moder else 5)
    )


async def order_choose_day(query: CallbackQuery):
    await BOT.edit_message_caption(query.message.chat.id, query.message.message_id, caption=texts.CHOOSE_DAY,
                                   reply_markup=await keyboards.order_choice_day())


async def order_cancel(query: CallbackQuery):
    await BOT.edit_message_caption(query.message.chat.id, query.message.message_id, caption=texts.ORDER_CANCELED,
                                   reply_markup=types.InlineKeyboardMarkup())
    await users.menu(query.message)


async def order_no_time(query: CallbackQuery, day: int, attempts: int):
    try:
        await BOT.edit_message_reply_markup(query.message.chat.id, query.message.message_id,
                                            reply_markup=await keyboards.order_choice_time(day, attempts - 1))
    except exceptions.MessageNotModified:
        pass
    await BOT.answer_callback_query(query.id, texts.ORDER_ERR_TOOLATE)


#


async def admin_choice(query: CallbackQuery, day: int, time: int, status: str):
    audio_name = get_by.get_audio_name(query.message.audio)
    user = get_by.get_user_from_entity(query.message)
    moder = query.from_user

    admin_text, also = await _gen_order_caption(day, time, user, status=status, moder=moder)
    await BOT.edit_message_caption(query.message.chat.id, query.message.message_id, caption=admin_text,
                                   reply_markup=keyboards.admin_unchoose(day, time, status))

    stats.add(audio_name, moder.id, user.id, status, str(datetime.now()), query.message.message_id)
    stats.change_username_to_id({user.username: user.id, moder.username: moder.id})

    if status == 'reject':  # кнопка отмена
        mes = await BOT.send_message(user.id, texts.ORDER_ERR_DENIED.format(audio_name, also['text_datetime']))
        return communication.cache_add(mes.message_id, query.message)

    path = _get_audio_path(day, time, audio_name)
    await files.download_audio(query.message.audio, path)
    await broadcast.radioboss.write_track_additional_info(path, user, query.message.message_id)

    if status == 'now':  # кнопка сейчас
        when_playing = 'прямо сейчас!'
        await broadcast.radioboss.radioboss_api(action='inserttrack', filename=path, pos=-2)
        mes = await BOT.send_message(user.id, texts.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))
        communication.cache_add(mes.message_id, query.message)

    if status == 'queue':  # кнопка принять

        if not also['now']:  # если щас не этот эфир то похуй
            when_playing = 'Заиграет когда надо'
            mes = await BOT.send_message(user.id, texts.ORDER_ACCEPTED.format(audio_name, also['text_datetime']))
            communication.cache_add(mes.message_id, query.message)
        elif await broadcast.playlist.find_in_playlist_by_path(path):
            when_playing = 'Такой же трек уже принят на этот эфир'
            mes = await BOT.send_message(user.id, texts.ORDER_ACCEPTED.format(audio_name, also['text_datetime']))
            communication.cache_add(mes.message_id, query.message)
        else:
            if last_track := await broadcast.playlist.get_new_order_pos():
                minutes_left = round((last_track.time_start - datetime.now()).seconds / 60)
                when_playing = f'через {minutes_left} ' + get_by.case_by_num(minutes_left, 'минуту', 'минуты', 'минут')

                await broadcast.radioboss.radioboss_api(action='inserttrack', filename=path, pos=last_track.index)
                mes = await BOT.send_message(user.id, texts.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))
                communication.cache_add(mes.message_id, query.message)
            else:
                when_playing = 'не успел :('
                mes = await BOT.send_audio(user.id, query.message.audio.file_id,
                                           reply_markup=await keyboards.order_choice_day(),
                                           caption=texts.ORDER_ERR_ACCEPTED_TOOLATE.
                                           format(audio_name, also['text_datetime']))
                communication.cache_add(mes.message_id, query.message)

    await BOT.edit_message_caption(query.message.chat.id, query.message.message_id,
                                   caption=admin_text + '\n🕑 ' + when_playing,
                                   reply_markup=keyboards.admin_unchoose(day, time, status))


async def admin_unchoice(query: CallbackQuery, day: int, time: int, status: str):
    user = get_by.get_user_from_entity(query.message)
    audio_name = get_by.get_audio_name(query.message.audio)
    admin_text, _ = await _gen_order_caption(day, time, user, audio_name=get_by.get_audio_name(query.message.audio))
    await BOT.edit_message_caption(ADMINS_CHAT_ID, query.message.message_id,
                                   caption=admin_text, reply_markup=keyboards.admin_choose(day, time))

    if status != 'reject':  # если заказ был принят а щас отменяют
        path = _get_audio_path(day, time, audio_name)
        files.delete_file(path)  # удалить с диска
        for track in await broadcast.playlist.find_in_playlist_by_path(path):
            await broadcast.radioboss.radioboss_api(action='delete', pos=track.index)


#

async def _gen_order_caption(day, time, user, audio_name=None, status=None, moder=None):
    async def get_bad_words_():
        if not (res := await music.get_bad_words(audio_name)):
            return ''

        title, b_w = res
        return f'<a href="https://{HOST}/gettext/{quote(audio_name[:100])}">' \
               f'{"⚠" if b_w else "🆗"} ({title})</a>  ' + ', '.join(b_w)  # ограничение по длинне ссылок

    is_now = broadcast.is_this_broadcast_now(day, time)
    is_now_text = ' (сейчас!)' if is_now else ''
    user_name = get_by.get_user_name(user)
    text_datetime = TIMES_NAME['week_days'][day] + ', ' + broadcast.get_broadcast_name(time)

    if not status:  # Неотмодеренный заказ
        is_now_mark = '‼️' if is_now else '❗️'
        bad_words = await get_bad_words_()
        is_anime = '🅰️' if await music.is_anime(audio_name) else ''
        text = f'{is_now_mark} Новый заказ - {text_datetime}{is_now_text} от {user_name}\n' \
               f'{bad_words}{is_anime} #отмодерить'
    else:
        status_text = "✅Принят" if status != 'reject' else "❌Отклонен"
        moder_name = get_by.get_user_name(moder)
        text = f'Заказ: {text_datetime}{is_now_text} от {user_name} {status_text} ({moder_name})'

    return text, {'text_datetime': text_datetime, 'now': is_now}


def _get_audio_path(day, time, audio_name):
    return broadcast.get_broadcast_path(day, time) / (audio_name + '.mp3')
