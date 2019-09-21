from config import *
from utils import other
from collections import OrderedDict


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
        await bot.send_message(ADMINS_CHAT_ID, "Ответ:", reply_to_message_id=reply_to)

    # todo print user link if hidden
    m = await bot.forward_message(ADMINS_CHAT_ID, message.chat.id, message.message_id)
    cache_add(m.message_id, message)


async def admin_message(message):
    if message.text and message.text.startswith("!"):  # игнор ответа
        return

    if cache_is_set(message.reply_to_message.message_id):  # если можно реплайнуть
        user, reply_to = cache_get(message.reply_to_message.message_id)

    else:  # если айдишника нету в кеше то пытаемся по старому
        if message.reply_to_message.audio:  # на заказ
            user = message.reply_to_message.caption_entities[0].user.id
            txt = "На ваш заказ <i>(" + other.get_audio_name(message.reply_to_message.audio) + ")</i> ответили:"

        elif message.reply_to_message.forward_date:  # на отзыв
            if not message.reply_to_message.forward_from:
                return await message.reply("Не могу ему написать")

            user = message.reply_to_message.forward_from.id
            txt = "На ваше сообщение ответили: "

        else:  # если админы реплайнули на какую то хуйню
            return

        reply_to = None
        await bot.send_message(user, txt)

    if message.audio:
        m = await bot.send_audio(user, message.audio.file_id, reply_to_message_id=reply_to)
    elif message.sticker:
        m = await bot.send_sticker(user, message.sticker.file_id, reply_to_message_id=reply_to)
    elif message.photo:
        m = await bot.send_photo(user, message.photo[-1].file_id, reply_to_message_id=reply_to, caption=message.caption)
    else:
        m = await bot.send_message(user, message.text, reply_to_message_id=reply_to, parse_mode='markdown')

    cache_add(m.message_id, message)

