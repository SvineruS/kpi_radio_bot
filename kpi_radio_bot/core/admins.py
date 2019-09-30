from config import *
from utils import other, radioboss, db, stats
from . import communication
import consts


async def ban(message):
    if message.reply_to_message is None or message.reply_to_message.from_user.id != (await bot.me).id:
        return await bot.send_message(message.chat.id, "Перешлите сообщение пользователя, которого нужно забанить")

    cmd = message.get_args().split(' ', 1)

    if communication.cache_is_set(message.reply_to_message.message_id):
        user, _ = communication.cache_get(message.reply_to_message.message_id)
    else:
        user = other.get_user_from_entity(message.reply_to_message)
        if not user:
            return await message.reply("Бля, не могу забанить")
        user = user.id

    ban_time = int(cmd[0]) if cmd[0].isdigit() else 60 * 24
    reason = f" Бан по причине: <i>{cmd[1]}</i>" if len(cmd) >= 2 else ""
    ban_time_text = str(ban_time) + ' ' + other.case_by_num(ban_time, 'минуту', 'минуты', 'минут')

    await db.ban_set(user, ban_time)

    if ban_time == 0:
        return await bot.send_message(message.chat.id, f"{other.get_user_name_(user, 'Пользователь')} разбанен")
    await bot.send_message(message.chat.id,
                           f"{other.get_user_name_(user, 'Пользователь')} забанен на {ban_time_text}. {reason}")
    await bot.send_message(user, consts.TextConstants.BAN_YOU_BANNED.format(ban_time_text, reason))


async def set_volume(message):
    if message.get_args().isdigit():
        volume = int(message.get_args())
        if 0 <= volume <= 100:
            await radioboss.radioboss_api(cmd=f'setvol {volume}')
            return await message.reply(f'Громкость выставлена в {volume}!')

    await message.reply(f'Головонька опухла! Громкость - число от 0 до 100, а не <code>{message.get_args()}</code>')


async def get_stats(message):
    if 'csv' in message.get_args():
        with open(PATH_STUFF / 'stats.csv', 'rb') as file:
            return await bot.send_document(message.chat.id, file)

    if len(message.entities) >= 2 and message.entities[1]['type'] == 'mention':
        moderator = message.entities[1].get_text(message.text)[1:]
        r = stats.line_plot(moderator)
        if r is False:
            return await message.reply(f"Хз кто такой {moderator}")
        caption = f"Стата модератора {moderator} ({r:.2f} модераций/дн.)"

    else:
        days = int(message.get_args()) if message.get_args().isdigit() else 7
        stats.bars_plot(days)
        caption = f'Стата за {days} дн.'

    with open(stats.PATH_STATS_PNG, 'rb') as file:
        await bot.send_photo(message.chat.id, file, caption=caption)
