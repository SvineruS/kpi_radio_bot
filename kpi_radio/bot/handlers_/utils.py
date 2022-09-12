import asyncio
import logging
from pathlib import Path

from consts import BOT, texts, config, others
from player import Ether, PlaylistItem, Broadcast
from utils import utils, db
from ..bot_utils import kb


async def send_ether_begin(time):
    await BOT.send_message(config.HISTORY_CHAT_ID, others.ETHER_NAMES[time])


async def send_history_track(track: PlaylistItem):
    sender_name = ''
    if info := track.track_info:
        sender_name = texts.HISTORY_TITLE.format(utils.get_user_name_(info.user_id, info.user_name))
        if db.Users.notification_get(info.user_id):
            await BOT.send_message(info.user_id, texts.ORDER_PLAYING.format(track))
        await BOT.edit_message_reply_markup(config.ADMINS_CHAT_ID, info.moderation_id, reply_markup=None)

    with track.path.open('rb') as file:
        await BOT.send_audio(config.HISTORY_CHAT_ID, file, sender_name, performer=track.performer, title=track.title)


async def perezaklad(ether: Ether):
    async def _send_perezaklad(user_id: int, path: Path):
        try:
            with path.open('rb') as file:
                await BOT.send_audio(user_id, file, caption=texts.ORDER_PEREZAKLAD,
                                     reply_markup=await kb.order_choose_day())
        except Exception as ex:
            logging.info(f"perezaklad err: {ex}")
            logging.warning(f"pls pls add exception {type(ex)}{ex} in except")

    tracks = await Broadcast(ether).playlist.get_playlist()
    for track in tracks:
        await _send_perezaklad(track.track_info.user_id, track.path)
        await asyncio.sleep(3)


async def send_startup_message():
    await BOT.send_message(config.ADMINS_CHAT_ID, texts.STARTUP_MESSAGE)
