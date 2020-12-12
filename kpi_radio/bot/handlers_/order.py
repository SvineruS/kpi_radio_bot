"""Обработка заказов"""

# todo refactor this
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from aiogram import types, exceptions

from player import Broadcast, files, exceptions as player_exceptions
import music
from consts import texts, others, config, BOT
from bot.handlers_ import users
from bot.bot_utils import communication, keyboards as kb, stats, id_to_hashtag
from utils import user_utils, get_by, db


async def order_make(query: types.CallbackQuery, broadcast: Broadcast):
    user = query.from_user
    user_db = db.Users.get_by_id(user.id)
    if user_db.is_banned():
        return await query.message.answer(texts.BAN_TRY_ORDER.format(user_db.banned_to()))

    try:
        await query.message.edit_caption(
            caption=texts.ORDER_ON_MODERATION.format(broadcast.name),
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
    admin_text = await _gen_order_caption(broadcast, user, status=status, moder=moder)

    try:
        await query.message.edit_caption(admin_text, reply_markup=kb.admin_unmoderate(broadcast, status))
    except exceptions.MessageNotModified:
        return  # если не отредачилось значит кнопка уже отработалась

    stats.add(query.message.message_id, moder.id, user.id, audio_name, status, datetime.now())

    if status == kb.STATUS.REJECT:  # кнопка отмена
        return communication.cache_add(
            await BOT.send_message(user.id, texts.ORDER_ERR_DENIED.format(audio_name, broadcast.name)), query.message)

    await query.message.chat.do('record_audio')
    try:
        new_track = await broadcast.add_track(
            query.message.audio,
            (user, query.message.message_id),
            position=0 if status == kb.STATUS.NOW else -1
        )
    except player_exceptions.DuplicateException:
        when_playing = 'Такой же трек уже принят на этот эфир'
        communication.cache_add(
            await BOT.send_message(user.id, texts.ORDER_ACCEPTED.format(audio_name, broadcast.name)), query.message)
    except player_exceptions.NotEnoughSpace:
        when_playing = 'не успел :('
        communication.cache_add(
            await BOT.send_audio(user.id, query.message.audio.file_id, reply_markup=await kb.order_choose_day(),
                                 caption=texts.ORDER_ERR_ACCEPTED_TOOLATE.format(audio_name, broadcast.name)),
            query.message)
    else:
        if status == kb.STATUS.NOW:  # кнопка сейчас
            when_playing = 'прямо сейчас!'
            mes = await BOT.send_message(user.id, texts.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing))
            communication.cache_add(mes, query.message)

        else:  # кнопка принять
            # если прямо сейчас не тот эфир, на который заказ
            if not broadcast.is_now():
                when_playing = 'Заиграет когда надо'
                communication.cache_add(
                    await BOT.send_message(user.id, texts.ORDER_ACCEPTED.format(audio_name, broadcast.name)),
                    query.message)

            else:
                minutes_left = round((new_track.time_start - datetime.now()).seconds / 60)
                when_playing = f'через {minutes_left} ' + get_by.case_by_num(minutes_left, 'минуту', 'минуты', 'минут')
                communication.cache_add(
                    await BOT.send_message(user.id, texts.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing)),
                    query.message)

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
        await broadcast.remove_track(path)


#

async def _gen_order_caption(broadcast: Broadcast, user: types.User,
                             audio_name: str = None, status: kb.STATUS = None, moder: types.User = None) -> str:
    is_now = broadcast.is_now()
    user_name = get_by.get_user_name(user) + ' #' + id_to_hashtag(user.id)
    text_datetime = broadcast.name + (' (сейчас!)' if is_now else '')

    if not status:  # Неотмодеренный заказ
        is_now_mark = '‼️' if is_now else '❗️'
        bad_words = await _get_bad_words_text(audio_name)
        is_anime = '🅰️' if await music.check.is_anime(audio_name) else ''

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
    if not (res := await music.check.get_bad_words(audio_name)):
        return ''

    title, b_w = res
    title = f'<a href="{_get_gettext_link(audio_name)}">{title}</a>'
    if not b_w:
        return "🆗" + title
    return f"⚠ {title}: " + ', '.join(b_w)


def _get_gettext_link(audio_name):
    return f"https://{config.HOST}/gettext/{quote(audio_name[:100])}"


def _get_audio_path(broadcast: Broadcast, audio_name: str) -> Path:
    return broadcast.path / (audio_name + '.mp3')
