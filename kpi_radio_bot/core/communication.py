"""Обеспечение удобного общения юзеров и админов на основе кеша и реплаев"""
from typing import Tuple

from aiogram.types import Message

import utils.get_by
from config import BOT, ADMINS_CHAT_ID
from utils.other import LRU

# key value db: to_message_id: (from_chat_id, from_message_id)
MESSAGES_CACHE = LRU(maxsize=1_000, ttl=60 * 60 * 24 * 3)


def cache_add(to_message: Message, from_message: Message):
    MESSAGES_CACHE[to_message.message_id] = (from_message.chat.id, from_message.message_id)


def cache_get(message_id: int) -> Tuple[int, int]:
    return MESSAGES_CACHE[message_id]


def cache_is_set(message_id: int) -> bool:
    return message_id in MESSAGES_CACHE


async def user_message(message: Message):
    if message.reply_to_message and cache_is_set(message.reply_to_message.message_id):
        _, reply_to = cache_get(message.reply_to_message.message_id)
    else:
        reply_to = None

    text = f"От {utils.get_by.get_user_name(message.from_user)}: \n"
    await _resend_message(message, ADMINS_CHAT_ID, additional_text=text, reply_to=reply_to)


async def admin_message(message: Message):
    if message.text and message.text.startswith("!"):  # игнор ответа
        return

    if cache_is_set(message.reply_to_message.message_id):
        user, reply_to = cache_get(message.reply_to_message.message_id)
        text = ''
    else:
        if not (user := utils.get_by.get_user_from_entity(message.reply_to_message)):
            return
        reply_to = None
        user = user.id

        if message.reply_to_message.audio:
            text = "На ваш заказ <i>(" + utils.get_by.get_audio_name(
                message.reply_to_message.audio) + ")</i> ответили: \n"
        else:
            text = "На ваше сообщение ответили: \n"

    await _resend_message(message, user, additional_text=text, reply_to=reply_to)


#


async def _resend_message(message: Message, chat: int, additional_text: str = '', reply_to: int = None):
    if additional_text and (message.audio or message.sticker):
        mes = await BOT.send_message(chat, additional_text)
        cache_add(mes, message)

    if message.audio:
        mes = await BOT.send_audio(chat, message.audio.file_id, reply_to_message_id=reply_to)
    elif message.sticker:
        mes = await BOT.send_sticker(chat, message.sticker.file_id, reply_to_message_id=reply_to)
    elif message.photo:
        mes = await BOT.send_photo(chat, message.photo[-1].file_id,
                                   caption=additional_text + (message.caption or ''), reply_to_message_id=reply_to)
    else:
        mes = await BOT.send_message(chat, additional_text + (message.text or ''), reply_to_message_id=reply_to)

    cache_add(mes, message)
