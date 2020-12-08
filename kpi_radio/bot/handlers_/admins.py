"""Обработка действий админов"""

import io
import os
from contextlib import suppress
from time import time
from typing import Tuple, Optional
from urllib.parse import unquote

from aiogram import types, exceptions

from player import Broadcast, Player
from consts import texts, config, BOT
from bot.bot_utils import communication, keyboards as kb, stats
from utils import user_utils, db, get_by


async def ban(message: types.Message):
    if message.reply_to_message is None or message.reply_to_message.from_user.id != (await BOT.me).id:
        return await message.reply("Перешлите сообщение пользователя, которого нужно забанить")

    if not (res := communication.get_from_message(message.reply_to_message)):
        return await message.reply("Бля, не могу забанить")
    user, _ = res

    ban_time, reason = _get_ban_time_and_reason_from_message(message)
    await db.users.ban_set(user, ban_time)

    if ban_time == 0:
        return await message.reply(f"{get_by.get_user_name_(user, 'Пользователь')} разбанен")

    ban_time_text = f'{ban_time} ' + get_by.case_by_num(ban_time, 'минуту', 'минуты', 'минут')
    await message.reply(f"{get_by.get_user_name_(user, 'Пользователь')} забанен на {ban_time_text}. {reason}")
    communication.cache_add(await BOT.send_message(user, texts.BAN_YOU_BANNED.format(ban_time_text, reason)), message)


async def set_volume(message: types.Message):
    if (volume := _get_volume_from_message(message)) is None:
        return await message.reply(f'Головонька опухла! Громкость - число от 0 до 100, а не <code>{volume}</code>')
    await Player.set_volume(volume)
    await message.reply(f'Громкость выставлена в {volume}!')


async def get_stats(message: types.Message):
    if 'csv' in message.get_args():
        await message.chat.do('upload_document')
        return await message.answer_document(stats.PATH_STATS_CSV.open('rb'))

    await message.chat.do('upload_photo')

    if len(message.entities) >= 2 and message.entities[1].type in ('mention', 'text_mention'):
        if not (moderator := await _get_moderator_from_mention(message)):
            return await message.reply(f"Хз кто это")
        if not (res := await stats.moder_stats(moderator.id)):
            return await message.reply(f"Он шото модерил ваще?")
        caption = f"Стата модератора {moderator.first_name} ({res:.2f} модераций/дн.)"

    else:
        days = int(message.get_args()) if message.get_args().isdigit() else 7
        await stats.all_moders_stats(days)
        caption = f'Стата за {days} дн.'

    await message.answer_photo(stats.PATH_STATS_PNG.open('rb'), caption=caption)


async def show_playlist_control(message: types.Message):
    await message.answer("Нажми на трек, что бы сделать его следующим", reply_markup=await kb.playlist_move())


async def playlist_move(query: types.CallbackQuery, track_index, track_start_time):
    pl = await Broadcast.now().get_playlist_next()
    _in_playback = [i for i, track in enumerate(pl) if
                    track.index_ == track_index and track.time_start.timestamp() == track_start_time]

    if track_index == -1:  # просто обновить
        pass
    elif time() > track_start_time or not _in_playback:
        await query.answer("Кнопка неактуальна, давай еще раз")
        pl = await Broadcast.now().get_playlist_next()
    elif _in_playback[0] == pl[1].index_:
        await query.answer("Она сейчас играет -_-")
    else:
        if await Player.set_next_track(track_index):
            pl.insert(1, pl.pop(_in_playback[0]))
            await query.answer("Успешно")
        else:
            await query.answer("Ошибка")

    with suppress(exceptions.MessageNotModified):
        await query.message.edit_reply_markup(await kb.playlist_move(pl))


async def get_log(message: types.Message):
    await message.chat.do('upload_document')
    text = config.PATH_LOG.read_text()
    text = unquote(text)  # unquote urls logged by aiohttp
    file = io.StringIO(text)
    file.name = 'log.txt'  # set filename
    await message.answer_document(file)


async def next_track(message: types.Message):
    if not await Player.next_track():
        await message.answer('хуй знает, не работает')
    prev, now, _ = await Broadcast.now().get_prev_now_next()
    await message.answer(f'<i>{prev} ➡ {now}</i>')


async def update(message: types.Message):
    await message.answer('Ребутаюсь..')
    os.system(rf'cmd.exe /C start {config.PATH_ROOT}\\update.bat')


#


def _get_ban_time_and_reason_from_message(message: types.Message) -> Tuple[int, str]:
    ban_time = 60 * 24
    reason = ''

    cmd = message.get_args().split(' ', maxsplit=1)
    if len(cmd) >= 1 and cmd[0].isdigit():
        ban_time = int(cmd[0])
    if len(cmd) >= 2:
        reason = f" Бан по причине: <i>{cmd[1]}</i>"

    return ban_time, reason


def _get_volume_from_message(message: types.Message) -> Optional[int]:
    if message.get_args().isdigit():
        volume = int(message.get_args())
        if 0 <= volume <= 100:
            return volume
    return None


async def _get_moderator_from_mention(message: types.Message) -> Optional[types.User]:
    if message.entities[1].type == 'mention':
        moderator = message.entities[1].get_text(message.text)[1:]
        return await user_utils.get_admin_by_username(moderator)
    else:
        return message.entities[1].user
