from config import *
from utils import other, radioboss, broadcast, db
from . import communication


async def ban(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return
    if message.reply_to_message is None:
        return await bot.send_message(message.chat.id, "Перешлите сообщение пользователя, которого нужно забанить")

    cmd = message.get_args().split(' ', 1)
    if message.reply_to_message.audio:  # на заказ
        user = message.reply_to_message.caption_entities[0].user
    elif message.reply_to_message.forward_date:  # на отзыв
        if message.reply_to_message.forward_from:
            user = message.reply_to_message.forward_from

        elif communication.cache_is_set(message.reply_to_message.message_id):
            user, _ = communication.cache_get(message.message_id)
        else:
            return await message.reply("Бля, не могу забанить")
    else:
        return

    ban_time = int(cmd[0]) if cmd[0].isdigit() else 60 * 24
    reason = f" Бан по причине: <i>{cmd[1]}</i>" if len(cmd) >= 2 else ""
    db.ban_set(user.id, ban_time)

    if ban_time == 0:
        return await bot.send_message(message.chat.id, f"{other.get_user_name(user)} разбанен")
    await bot.send_message(message.chat.id, f"{other.get_user_name(user)} забанен на {ban_time} минут. {reason}")
    await bot.send_message(user.id, f"Вы были забанены на {ban_time} минут. {reason}")


async def set_volume(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return

    if not broadcast.is_broadcast_right_now():
        return await message.reply("Богдан пошел нахуй" if message.from_user.id == 337283845 else
                                   "Только во время эфира")

    if message.get_args().isdigit():
        volume = int(message.get_args())
        if 0 <= volume <= 100:
            await radioboss.radioboss_api(cmd=f'setvol {volume}')
            return await message.reply(f'Громкость выставлена в {volume}!')

    await message.reply(f'Головонька опухла! Громкость - число от 0 до 100, а не <code>{message.get_args()}</code>')


async def get_stats(message):
    if message.chat.id != ADMINS_CHAT_ID:
        return

    if 'csv' in message.get_args():
        with open(PATH_STUFF / 'stats.csv', 'rb') as file:
            await bot.send_document(message.chat.id, file)
    else:
        days = int(message.get_args()) if message.get_args().isdigit() else 7
        other.gen_stats_graph(days)
        with open(PATH_STUFF / 'stats.png', 'rb') as file:
            await bot.send_photo(message.chat.id, file, caption=f'Стата за {days} дн.')
