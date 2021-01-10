import asyncio
import logging
from pathlib import Path

from consts import BOT, texts, config, others
from player import Broadcast
from player.player_utils import files, TrackInfo
from utils import utils, db
from ..bot_utils import kb


async def send_broadcast_begin(time):
    await BOT.send_message(config.HISTORY_CHAT_ID, others.TIMES[time])


async def send_history_track(path: Path, performer: str, title: str):
    sender_name = ''
    if tag := await TrackInfo.read(path):
        sender_name = texts.HISTORY_TITLE.format(utils.get_user_name_(tag.id, tag.name))
        if db.Users.notification_get(tag.id):
            await BOT.send_message(tag.id, texts.ORDER_PLAYING.format(utils.get_audio_name_(performer, title)))
        await BOT.edit_message_reply_markup(config.ADMINS_CHAT_ID, tag.moderation_id, reply_markup=None)

    await TrackInfo.clear(path)  # Очистить тег, что бы уведомление не пришло еще раз

    with path.open('rb') as file:
        await BOT.send_audio(config.HISTORY_CHAT_ID, file, sender_name, performer=performer, title=title)


async def perezaklad(day, time):
    # radioboss specific

    async def _send_perezaklad(user_id: int, path: Path):
        try:
            with path.open('rb') as file:
                await BOT.send_audio(user_id, file, caption=texts.ORDER_PEREZAKLAD,
                                     reply_markup=await kb.order_choose_day())
        except Exception as ex:
            logging.info(f"perezaklad err: {ex}")
            logging.warning(f"pls pls add exception {type(ex)}{ex} in except")

    tracks = files.get_downloaded_tracks(Broadcast(day, time).path)
    for track_path in tracks:
        if tag := await TrackInfo.read(track_path):
            await _send_perezaklad(tag.id, track_path)
            await asyncio.sleep(3)


async def send_startup_message():
    await BOT.send_message(config.ADMINS_CHAT_ID, "Ребутнулся!")
