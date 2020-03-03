"""Обработка заказов"""

# todo refactor this
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from aiogram import types, exceptions

import backend.music.check
import frontend.frontend_utils.id_to_hashtag
from backend import playlist, radioboss, files, Broadcast
from consts import texts, others, config, BOT
from frontend.core import users
from frontend.frontend_utils import communication, keyboards as kb, stats
from utils import user_utils, db, get_by


async def order_make(query: types.CallbackQuery, broadcast: Broadcast):
    user = query.from_user
    if is_ban := await db.ban_get(user.id):
        return await query.message.answer(texts.BAN_TRY_ORDER.format(is_ban.strftime("%d.%m %H:%M")))

    try:
        await query.message.edit_caption(
            caption=texts.ORDER_ON_MODERATION.format(broadcast.name()),
            reply_markup=types.InlineKeyboardMarkup(),
        )
    except exceptions.MessageNotModified:
        return  # если не отредачилось значит кидать второе меню тоже не нужно

    await users.menu(query.message)

    admin_text = await _gen_order_caption(broadcast, user, audio_name=get_by.get_audio_name(query.message.audio))
    mes = await BOT.send_audio(config.ADMINS_CHAT_ID, query.message.audio.file_id, admin_text,
                               reply_markup=kb.admin_moderate(broadcast))
    communication.cache_add(mes, query.message)
    communication.cache_add(query.message, mes)


async def order_choose_time(query: types.CallbackQuery, day: int):
    is_moder = await user_utils.is_admin(query.from_user.id)
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_caption(
            caption=texts.CHOOSE_TIME.format(others.WEEK_DAYS[day]),
            reply_markup=await kb.order_choose_time(day, 0 if is_moder else 5)
        )


async def order_choose_day(query: types.CallbackQuery):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_caption(texts.CHOOSE_DAY, reply_markup=await kb.order_choose_day())


async def order_cancel(query: types.CallbackQuery):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_caption(texts.ORDER_CANCELED, reply_markup=types.InlineKeyboardMarkup())
        await users.menu(query.message)


async def order_no_time(query: types.CallbackQuery, day: int, attempts: int):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_reply_markup(await kb.order_choose_time(day, attempts - 1))
    await query.answer(texts.ORDER_ERR_TOOLATE)


#


async def admin_moderate(query: types.CallbackQuery, broadcast: Broadcast, status: kb.STATUS):
    user = get_by.get_user_from_entity(query.message)
    moder = query.from_user
    audio_name = get_by.get_audio_name(query.message.audio)
    text_datetime = broadcast.name()
    admin_text = await _gen_order_caption(broadcast, user, status=status, moder=moder)

    try:
        await query.message.edit_caption(admin_text, reply_markup=kb.admin_unmoderate(broadcast, status))
    except exceptions.MessageNotModified:
        return  # если не отредачилось значит кнопка уже отработалась

    stats.add(audio_name, moder.id, user.id, status, str(datetime.now()), query.message.message_id)
    stats.change_username_to_id({user.username: user.id, moder.username: moder.id})

    if status == kb.STATUS.REJECT:  # кнопка отмена
        mes = await BOT.send_message(user.id, texts.ORDER_ERR_DENIED.format(audio_name, text_datetime))
        return communication.cache_add(mes, query.message)

    path = _get_audio_path(broadcast, audio_name)
    await query.message.chat.do('record_audio')
    await files.download_audio(query.message.audio, path)
    await radioboss.write_track_additional_info(path, user, query.message.message_id)

    if status == kb.STATUS.NOW:  # кнопка сейчас
        when_playing = 'прямо сейчас!'
        await radioboss.inserttrack(path, -2)
        mes = await BOT.send_message(user.id, texts.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))
        communication.cache_add(mes, query.message)

    else:  # кнопка принять

        # если прямо сейчас не тот эфир, на который заказ
        if not broadcast.is_now():
            when_playing = 'Заиграет когда надо'
            mes = await BOT.send_message(user.id, texts.ORDER_ACCEPTED.format(audio_name, text_datetime))
            communication.cache_add(mes, query.message)

        # тут и ниже - трек заказан на эфир, который сейчас играет

        # если такой трек уже есть в плейлисте
        elif await playlist.find_in_playlist_by_path(path):
            when_playing = 'Такой же трек уже принят на этот эфир'
            mes = await BOT.send_message(user.id, texts.ORDER_ACCEPTED.format(audio_name, text_datetime))
            communication.cache_add(mes, query.message)

        # в плейлисте есть место для заказа
        elif last_track := await broadcast.get_new_order_pos():
            minutes_left = round((last_track.time_start - datetime.now()).seconds / 60)
            when_playing = f'через {minutes_left} ' + get_by.case_by_num(minutes_left, 'минуту', 'минуты', 'минут')

            await radioboss.inserttrack(path, last_track.index_)
            mes = await BOT.send_message(user.id, texts.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))
            communication.cache_add(mes, query.message)

        # в плейлисте нету места
        else:
            when_playing = 'не успел :('
            mes = await BOT.send_audio(
                user.id, query.message.audio.file_id, reply_markup=await kb.order_choose_day(),
                caption=texts.ORDER_ERR_ACCEPTED_TOOLATE.format(audio_name, text_datetime)
            )
            communication.cache_add(mes, query.message)

    with suppress(exceptions.MessageNotModified):
        await query.message.edit_caption(admin_text + '\n🕑 ' + when_playing,
                                         reply_markup=kb.admin_unmoderate(broadcast, status))


async def admin_unmoderate(query: types.CallbackQuery, broadcast: Broadcast, status: kb.STATUS):
    user = get_by.get_user_from_entity(query.message)
    audio_name = get_by.get_audio_name(query.message.audio)
    admin_text = await _gen_order_caption(broadcast, user, audio_name=get_by.get_audio_name(query.message.audio))

    try:
        await query.message.edit_caption(admin_text, reply_markup=kb.admin_moderate(broadcast))
    except exceptions.MessageNotModified:
        return  # если не отредачилось значит кнопка уже отработалась

    if status != kb.STATUS.REJECT:  # если заказ был принят а щас отменяют
        path = _get_audio_path(broadcast, audio_name)
        files.delete_file(path)  # удалить с диска
        for track in await playlist.find_in_playlist_by_path(path):
            await radioboss.delete(track.index_)


#

async def _gen_order_caption(broadcast: Broadcast, user: types.User,
                             audio_name: str = None, status: kb.STATUS = None, moder: types.User = None) -> str:
    is_now = broadcast.is_now()
    user_name = get_by.get_user_name(user) + ' #' + frontend.frontend_utils.id_to_hashtag(user.id)
    text_datetime = broadcast.name() + (' (сейчас!)' if is_now else '')

    if not status:  # Неотмодеренный заказ
        is_now_mark = '‼️' if is_now else '❗️'
        bad_words = await _get_bad_words_text(audio_name)
        is_anime = '🅰️' if await backend.music.check.is_anime(audio_name) else ''

        return f'{is_now_mark} Новый заказ: \n' \
               f'{text_datetime} \n' \
               f'от {user_name}<code>   </code>{texts.HASHTAG_MODERATE}\n' \
               f'{is_anime}{bad_words}'
    else:
        status_text = "✅Принят" if status != kb.STATUS.REJECT else "❌Отклонен"
        moder_name = get_by.get_user_name(moder)

        return f'Заказ: \n' \
               f'{text_datetime}\n' \
               f'от {user_name}\n' \
               f'{status_text} ({moder_name})'


async def _get_bad_words_text(audio_name: str) -> str:
    if not (res := await backend.music.check.get_bad_words(audio_name)):
        return ''

    title, b_w = res
    title = f'<a href="https://{config.HOST}/gettext/{quote(audio_name[:100])}">{title}</a>'
    if not b_w:
        return "🆗" + title
    return f"⚠ {title}: " + ', '.join(b_w)


def _get_audio_path(broadcast: Broadcast, audio_name: str) -> Path:
    return broadcast.path() / (audio_name + '.mp3')