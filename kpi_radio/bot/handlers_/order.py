"""Обработка заказов"""

from contextlib import suppress
from urllib.parse import quote

from aiogram import types, exceptions

import music
from bot import handlers_
from bot.bot_utils import communication, kb, stats, id_to_hashtag
from consts import texts, others, config, BOT
from player import Broadcast, exceptions as player_exceptions
from utils import utils, db, DateTime


async def order_make(query: types.CallbackQuery, broadcast: Broadcast):
    user = query.from_user
    user_db = db.Users.get(user.id)
    if user_db.is_banned():
        return await query.message.answer(texts.BAN_TRY_ORDER.format(user_db.banned_to()))

    try:
        await query.message.edit_caption(
            caption=texts.ORDER_ON_MODERATION.format(broadcast.name),
            reply_markup=types.InlineKeyboardMarkup(),
        )
    except exceptions.MessageNotModified:
        return  # если не отредачилось значит кидать второе меню тоже не нужно

    await handlers_.users.menu(query.message)

    admin_text = await _gen_order_caption(broadcast, user, audio_name=utils.get_audio_name(query.message.audio))
    mes = await BOT.send_audio(config.ADMINS_CHAT_ID, query.message.audio.file_id, admin_text,
                               reply_markup=kb.admin_moderate(broadcast))
    communication.cache_add(mes, query.message)
    communication.cache_add(query.message, mes)


async def order_choose_time(query: types.CallbackQuery, day: int):
    is_moder = await utils.is_admin(query.from_user.id)
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
        await handlers_.users.menu(query.message)


async def order_no_time(query: types.CallbackQuery, day: int, attempts: int):
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_reply_markup(await kb.order_choose_time(day, attempts - 1))
    await query.answer(texts.ORDER_ERR_TOOLATE)


#


async def admin_moderate(query: types.CallbackQuery, broadcast: Broadcast, status: kb.STATUS):
    user = utils.get_user_from_entity(query.message)
    moder = query.from_user
    audio_name = utils.get_audio_name(query.message.audio)
    admin_text = await _gen_order_caption(broadcast, user, status=status, moder=moder)

    try:
        await query.message.edit_caption(admin_text, reply_markup=kb.admin_unmoderate(broadcast, status))
    except exceptions.MessageNotModified:
        return  # если не отредачилось значит кнопка уже отработалась

    stats.add(query.message.message_id, moder.id, user.id, audio_name, status, DateTime.now())

    if status == kb.STATUS.REJECT:  # кнопка отмена
        return communication.cache_add(
            await BOT.send_message(user.id, texts.ORDER_ERR_DENIED.format(audio_name, broadcast.name)), query.message)

    await query.message.chat.do('record_audio')
    try:
        new_track = await broadcast.add_track(query.message.audio, (user, query.message.message_id),
                                              position=0 if status == kb.STATUS.NOW else -1)
    except player_exceptions.DuplicateException:
        when_playing = 'Такой же трек уже принят на этот эфир'
        msg_to_user = texts.ORDER_ACCEPTED.format(audio_name, broadcast.name)
    except player_exceptions.NotEnoughSpace:
        when_playing = 'не успел :('
        msg_to_user = None
        communication.cache_add(await BOT.send_audio(
            user.id, query.message.audio.file_id, reply_markup=await kb.order_choose_day(),
            caption=texts.ORDER_ACCEPTED_TOOLATE.format(audio_name, broadcast.name)), query.message
        )
    else:
        if status == kb.STATUS.NOW:  # кнопка сейчас
            when_playing = 'прямо сейчас!'
            msg_to_user = texts.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing)

        else:  # кнопка принять
            # если прямо сейчас не тот эфир, на который заказ
            if not broadcast.is_now():
                when_playing = 'Заиграет когда надо'
                msg_to_user = texts.ORDER_ACCEPTED.format(audio_name, broadcast.name)

            else:
                minutes_left = round((new_track.time_start - DateTime.now()).seconds / 60)
                when_playing = f'через {minutes_left} ' + utils.case_by_num(minutes_left, 'минуту', 'минуты', 'минут')
                msg_to_user = texts.ORDER_ACCEPTED_UPNEXT.format(audio_name, when_playing)

    if msg_to_user:
        communication.cache_add(await BOT.send_message(user.id, msg_to_user), query.message)
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_caption(admin_text + '\n🕑 ' + when_playing,
                                         reply_markup=kb.admin_unmoderate(broadcast, status))


async def admin_unmoderate(query: types.CallbackQuery, broadcast: Broadcast, status: kb.STATUS):
    user = utils.get_user_from_entity(query.message)
    admin_text = await _gen_order_caption(broadcast, user, audio_name=utils.get_audio_name(query.message.audio))

    try:
        await query.message.edit_caption(admin_text, reply_markup=kb.admin_moderate(broadcast))
    except exceptions.MessageNotModified:
        return  # если не отредачилось значит кнопка уже отработалась

    if status != kb.STATUS.REJECT:  # если заказ был принят а щас отменяют
        await broadcast.remove_track(query.message.audio)


#

async def _gen_order_caption(broadcast: Broadcast, user: types.User,
                             audio_name: str = None, status: kb.STATUS = None, moder: types.User = None) -> str:
    is_now = broadcast.is_now()
    user_name = utils.get_user_name(user) + ' #' + id_to_hashtag(user.id)
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
        moder_name = utils.get_user_name(moder)

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
