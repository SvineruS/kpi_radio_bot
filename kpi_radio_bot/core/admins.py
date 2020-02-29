"""Обработка действий админов"""

import io
import os
from time import time
from urllib.parse import unquote

from aiogram import types, exceptions

from consts import texts, keyboards
from broadcast import radioboss, playlist
from config import BOT, PATH_STUFF, PATH_LOG, PATH_ROOT
from core import communication
from utils import user_utils, db, stats, get_by


async def ban(message: types.Message):
    if message.reply_to_message is None or message.reply_to_message.from_user.id != (await BOT.me).id:
        return await message.reply("Перешлите сообщение пользователя, которого нужно забанить")

    cmd = message.get_args().split(' ', 1)

    if communication.cache_is_set(message.reply_to_message.message_id):
        user, _ = communication.cache_get(message.reply_to_message.message_id)
    else:
        if not (user := get_by.get_user_from_entity(message.reply_to_message)):
            return await message.reply("Бля, не могу забанить")
        user = user.id

    ban_time = int(cmd[0]) if cmd[0].isdigit() else 60 * 24
    reason = f" Бан по причине: <i>{cmd[1]}</i>" if len(cmd) >= 2 else ""
    ban_time_text = str(ban_time) + ' ' + get_by.case_by_num(ban_time, 'минуту', 'минуты', 'минут')

    await db.ban_set(user, ban_time)

    if ban_time == 0:
        return await message.answer(f"{get_by.get_user_name_(user, 'Пользователь')} разбанен")
    await message.answer(f"{get_by.get_user_name_(user, 'Пользователь')} забанен на {ban_time_text}. {reason}")
    await BOT.send_message(user, texts.BAN_YOU_BANNED.format(ban_time_text, reason))


async def set_volume(message: types.Message):
    if message.get_args().isdigit():
        volume = int(message.get_args())
        if 0 <= volume <= 100:
            await radioboss.setvol(volume)
            return await message.reply(f'Громкость выставлена в {volume}!')

    await message.reply(f'Головонька опухла! Громкость - число от 0 до 100, а не <code>{message.get_args()}</code>')


async def get_stats(message: types.Message):
    if 'csv' in message.get_args():
        await BOT.send_chat_action(message.chat.id, 'upload_document')
        return await message.answer_document((PATH_STUFF / 'stats.csv').open('rb'))

    await BOT.send_chat_action(message.chat.id, 'upload_photo')

    if len(message.entities) >= 2 and message.entities[1].type in ('mention', 'text_mention'):
        if message.entities[1].type == 'mention':
            moderator = message.entities[1].get_text(message.text)[1:]
            moderator = (await user_utils.get_admin_by_username(moderator))
        else:
            moderator = message.entities[1].user

        res = await stats.line_plot(moderator.id)
        if res is False:
            return await message.reply(f"Хз кто это")
        caption = f"Стата модератора {moderator.first_name} ({res:.2f} модераций/дн.)"

    else:
        days = int(message.get_args()) if message.get_args().isdigit() else 7
        await stats.bars_plot(days)
        caption = f'Стата за {days} дн.'

    await message.answer_photo(stats.PATH_STATS_PNG.open('rb'), caption=caption)


async def show_playlist_control(message: types.Message):
    await message.answer("Нажми на трек, что бы сделать его следующим", reply_markup=await keyboards.playlist_move())


async def playlist_move(query: types.CallbackQuery, track_index, track_start_time):
    playback = await playlist.get_next()
    _in_playback = [i for i, track in enumerate(playback) if
                    track.index == track_index and track.time_start.timestamp() == track_start_time]

    if track_index == -1:  # просто обновить
        pass
    elif time() > track_start_time or not _in_playback:
        await query.answer("Кнопка неактуальна, давай еще раз")
        playback = await playlist.get_next()
    elif _in_playback[0] == playback[1].index:
        await query.answer("Она сейчас играет -_-")
    else:
        if await radioboss.move(track_index, playback[1].index):
            playback.insert(1, playback.pop(_in_playback[0]))
            await query.answer("Успешно")
        else:
            await query.answer("Ошибка")

    try:
        await query.message.edit_reply_markup(await keyboards.playlist_move(playback))
    except exceptions.MessageNotModified:
        pass


async def get_log(message: types.Message):
    await BOT.send_chat_action(message.chat.id, 'upload_document')
    text = PATH_LOG.read_text()
    text = unquote(text)  # unquote urls logged by aiohttp
    file = io.StringIO(text)
    file.name = 'log.txt'  # set filename
    await message.answer_document(file)


async def next_track(message: types.Message):
    if not await radioboss.next():
        await message.answer('хуй знает, не работает')
    prev, now, _ = await playlist.get_now()
    await message.answer(f'<i>{prev} ➡ {now}</i>')


async def update(message: types.Message):
    await message.answer('Ребутаюсь..')
    os.system(rf'cmd.exe /C start {PATH_ROOT}\\update.bat')
