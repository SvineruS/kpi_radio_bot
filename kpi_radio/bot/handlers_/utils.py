import logging
from pathlib import Path

from consts import BOT, texts, config, others
from player.player_utils import track_info
from utils import utils, db
from ..bot_utils import kb


async def send_broadcast_begin(time):
    await BOT.send_message(config.HISTORY_CHAT_ID, others.TIMES[time])


async def send_history_track(path: Path, performer: str, title: str):
    sender_name = ''
    if tag := await track_info.read(path):
        sender_name = texts.HISTORY_TITLE.format(utils.get_user_name_(tag['id'], tag['name']))
        if db.Users.notification_get(tag['id']):
            await BOT.send_message(tag['id'], texts.ORDER_PLAYING.format(utils.get_audio_name_(performer, title)))
        await BOT.edit_message_reply_markup(config.ADMINS_CHAT_ID, tag['moderation_id'], reply_markup=None)

    await track_info.clear(path)  # Очистить тег, что бы уведомление не пришло еще раз

    with path.open('rb') as file:
        await BOT.send_audio(config.HISTORY_CHAT_ID, file, sender_name, performer=performer, title=title)


async def send_perezaklad(user_id: int, path: Path):
    with path.open('rb') as file:
        try:
            await BOT.send_audio(user_id, file, caption=texts.ORDER_PEREZAKLAD,
                                 reply_markup=await kb.order_choose_day())
        except Exception as ex:
            logging.info(f"perezaklad send msg: {ex}")
            logging.warning(f"pls pls add exception {type(ex)}{ex} in except")


async def send_startup_message():
    await BOT.send_message(config.ADMINS_CHAT_ID, "Ребутнулся!")
