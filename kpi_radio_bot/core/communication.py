from collections import OrderedDict

from config import bot, ADMINS_CHAT_ID
from utils import other

# key value db: to_message_id: (from_chat_id, from_message_id)
MESSAGES_CACHE = OrderedDict()
MAX_LENGTH = 10000


def cache_add(to_msg_id, from_message):
    MESSAGES_CACHE[to_msg_id] = (from_message.chat.id, from_message.message_id)
    while len(MESSAGES_CACHE) > MAX_LENGTH:
        MESSAGES_CACHE.popitem(last=False)  # pop older


def cache_get(message_id):
    return MESSAGES_CACHE.get(message_id, None)


def cache_is_set(message_id):
    return message_id in MESSAGES_CACHE


async def user_message(message):
    if message.reply_to_message and cache_is_set(message.reply_to_message.message_id):
        _, reply_to = cache_get(message.reply_to_message.message_id)
    else:
        reply_to = None

    text = f"От {other.get_user_name(message.from_user)}: \n"
    await resend_message(message, ADMINS_CHAT_ID, additional_text=text, reply_to=reply_to)


async def admin_message(message):
    if message.text and message.text.startswith("!"):  # игнор ответа
        return

    if cache_is_set(message.reply_to_message.message_id):
        user, reply_to = cache_get(message.reply_to_message.message_id)
        text = ''
    else:
        user = other.get_user_from_entity(message.reply_to_message)
        reply_to = None
        if not user:
            return
        user = user.id

        if message.reply_to_message.audio:
            text = "На ваш заказ <i>(" + other.get_audio_name(message.reply_to_message.audio) + ")</i> ответили: \n"
        else:
            text = "На ваше сообщение ответили: \n"

    await resend_message(message, user, additional_text=text, reply_to=reply_to)


async def resend_message(message, chat, additional_text='', reply_to=None):
    if additional_text and (message.audio or message.sticker):
        message = await bot.send_message(chat, additional_text)
        cache_add(message.message_id, message)

    if message.audio:
        message = await bot.send_audio(chat, message.audio.file_id, reply_to_message_id=reply_to)
    elif message.sticker:
        message = await bot.send_sticker(chat, message.sticker.file_id, reply_to_message_id=reply_to)
    elif message.photo:
        message = await bot.send_photo(chat, message.photo[-1].file_id,
                                       caption=additional_text + (message.caption or ''), reply_to_message_id=reply_to)
    else:
        message = await bot.send_message(chat, additional_text + (message.text or ''), reply_to_message_id=reply_to)

    cache_add(message.message_id, message)
