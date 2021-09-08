"""Обработка заказов"""

from contextlib import suppress
from typing import Optional
from urllib.parse import quote

from aiogram import types, exceptions

import music
from bot import handlers_
from bot.bot_utils import communication, kb, stats, id_to_hashtag, small_utils
from consts import texts, others, config, BOT
from player import Broadcast, Ether, PlaylistItem
from utils import utils, db, DateTime


NotEnoughSpaceException = type("NotEnoughSpace", (Exception, ), {})
DuplicateException = type("DuplicateException", (Exception, ), {})
BannedException = type("BannedException", (Exception, ), {})
TooManyOrdersException = type("BannedException", (Exception, ), {})


async def order_make(query: types.CallbackQuery, ether: Ether):
    try:
        await _can_make_order(ether, query.from_user)
    except BannedException as be:
        return await query.message.answer(texts.BAN_TRY_ORDER.format(be.arg))
    except TooManyOrdersException:
        return await query.message.answer(texts.ORDER_ERR_TOOMUCH)

    try:
        await query.message.edit_caption(
            caption=texts.ORDER_ON_MODERATION.format(ether.name),
            reply_markup=types.InlineKeyboardMarkup(),
        )
    except exceptions.MessageNotModified:
        return  # если не отредачилось значит кидать второе меню тоже не нужно

    await handlers_.users.menu(query.message)

    admin_text = await _gen_order_caption(ether, query.from_user, audio_name=utils.get_audio_name(query.message.audio))
    mes = await BOT.send_audio(config.ADMINS_CHAT_ID, query.message.audio.file_id, admin_text,
                               reply_markup=kb.admin_moderate(ether))
    communication.cache_add(mes, query.message)
    communication.cache_add(query.message, mes)


async def order_choose_time(query: types.CallbackQuery, day: int):
    is_moder = await small_utils.is_admin(query.from_user.id)
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


async def admin_moderate(query: types.CallbackQuery, ether: Ether, status: kb.STATUS):
    user = utils.get_user_from_entity(query.message)
    moder = query.from_user
    admin_text = await _gen_order_caption(ether, user, status=status, moder=moder)
    track = PlaylistItem.from_tg(query.message.audio).add_track_info(user.id, user.first_name, query.message.message_id)

    try:
        await query.message.edit_caption(admin_text, reply_markup=kb.admin_unmoderate(ether, status))
    except exceptions.MessageNotModified:
        return  # если не отредачилось значит кнопка уже отработалась

    stats.add(query.message.message_id, moder.id, user.id, str(track), status, DateTime.now())

    if status == kb.STATUS.REJECT:  # кнопка отмена
        return communication.cache_add(
            await BOT.send_message(user.id, texts.ORDER_DENIED.format(track, ether.name)), query.message)

    await query.message.chat.do('record_audio')
    msg_to_user: Optional[str]
    try:
        if status != kb.STATUS.NOW:
            await _can_approve_order(ether, query.message.audio)
        ether_ = None if status == kb.STATUS.NOW else ether
        new_track = await Broadcast(ether_).add_track(track, audio=query.message.audio)

    except DuplicateException:
        when_playing = 'Такой же трек уже принят на этот эфир'
        msg_to_user = texts.ORDER_ACCEPTED.format(track, ether.name)
    except NotEnoughSpaceException:
        when_playing = 'не успел :('
        msg_to_user = None
        communication.cache_add(await BOT.send_audio(
            user.id, query.message.audio.file_id, reply_markup=await kb.order_choose_day(),
            caption=texts.ORDER_ACCEPTED_TOOLATE.format(track, ether.name)), query.message
        )
    else:
        if status == kb.STATUS.NOW:
            when_playing = 'прямо сейчас!'
            msg_to_user = texts.ORDER_ACCEPTED_UPNEXT.format(track, when_playing)
        elif ether.is_now():
            minutes_left = round((new_track.start_time - DateTime.now()).seconds / 60)
            when_playing = f'через {minutes_left} ' + utils.case_by_num(minutes_left, 'минуту', 'минуты', 'минут')
            msg_to_user = texts.ORDER_ACCEPTED_UPNEXT.format(track, when_playing)
        else:
            when_playing = 'Заиграет когда надо'
            msg_to_user = texts.ORDER_ACCEPTED.format(track, ether.name)

    if msg_to_user:
        communication.cache_add(await BOT.send_message(user.id, msg_to_user), query.message)
    with suppress(exceptions.MessageNotModified):
        await query.message.edit_caption(admin_text + '\n🕑 ' + when_playing, reply_markup=kb.admin_unmoderate(ether, status))


async def admin_unmoderate(query: types.CallbackQuery, ether: Ether, status: kb.STATUS):
    user = utils.get_user_from_entity(query.message)
    admin_text = await _gen_order_caption(ether, user, audio_name=utils.get_audio_name(query.message.audio))

    try:
        await query.message.edit_caption(admin_text, reply_markup=kb.admin_moderate(ether))
    except exceptions.MessageNotModified:
        return  # если не отредачилось значит кнопка уже отработалась

    if status != kb.STATUS.REJECT:  # если заказ был принят а щас отменяют
        await Broadcast(ether).remove_track(PlaylistItem.from_tg(query.message.audio))


#


async def _can_make_order(ether: Ether, user: types.User):
    if banned_to := db.Users.get(user.id).banned_to():
        raise BannedException(banned_to)

    pl = await Broadcast(ether).get_next_tracklist()

    if ether.num != 5 and len(pl.find_by_user_id(user.id)) > 5:
        raise TooManyOrdersException()


async def _can_approve_order(ether: Ether, audio: types.Audio):
    br = Broadcast(ether)
    pl = await br.get_next_tracklist()

    if pl.find_by_path(PlaylistItem.from_tg(audio).path):
        raise DuplicateException()

    if await br.get_free_time(pl) < audio.duration:
        raise NotEnoughSpaceException()


async def _gen_order_caption(ether: Ether, user: types.User,
                             audio_name: str = None, status: kb.STATUS = None, moder: types.User = None) -> str:
    is_now = ether.is_now()
    user_name = utils.get_user_name(user) + ' #' + id_to_hashtag(user.id)
    text_datetime = ether.name + (' (сейчас!)' if is_now else '')

    if not status:  # Неотмодеренный заказ
        assert audio_name is not None
        is_now_mark = '‼️' if is_now else '❗️'
        bad_words = await _get_bad_words_text(audio_name)
        is_anime = '🅰️' if await music.check.is_anime(audio_name) else ''

        return f'{is_now_mark} Новый заказ: \n' \
               f'{text_datetime} \n' \
               f'от {user_name}<code>   </code>{texts.HASHTAG_MODERATE}\n' \
               f'{is_anime}{bad_words}'
    else:
        assert moder is not None
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


def _get_gettext_link(audio_name: str) -> str:
    return f"https://{config.HOST}/gettext/{quote(audio_name[:100])}"
