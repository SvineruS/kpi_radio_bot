"""Обработка ивентов (начало перерыва, заиграл трек, ...)"""

import asyncio
import logging

import consts
from broadcast import radioboss, broadcast
from config import HISTORY_CHAT_ID, BOT, ADMINS_CHAT_ID
from consts import keyboards
from utils import get_by, db, files


async def send_history(fields):
    if not broadcast.is_broadcast_right_now():  # кидать только во время перерыва
        return

    if not fields['artist'] and not fields['title']:
        fields['title'] = fields['casttitle']

    sender_name = ''
    tag = await radioboss.read_track_additional_info(fields['path'])
    await radioboss.clear_track_additional_info(fields['path'])  # Очистить тег, что бы уведомление не пришло еще раз

    if tag:
        sender_name = consts.texts.HISTORY_TITLE.format(get_by.get_user_name_(tag['id'], tag['name']))
        if not await db.notification_get(tag['id']):
            await BOT.send_message(tag['id'], consts.texts.ORDER_PLAYING.format(fields['casttitle']))
        await BOT.edit_message_reply_markup(ADMINS_CHAT_ID, tag['moderation_id'], reply_markup=None)

    with open(fields['path'], 'rb') as file:
        await BOT.send_audio(HISTORY_CHAT_ID, file, sender_name, performer=fields['artist'], title=fields['title'])


async def broadcast_begin(time):
    await BOT.send_message(HISTORY_CHAT_ID, broadcast.get_broadcast_name(time))
    await radioboss.radioboss_api(cmd='setvol 100')  # включить музло на перерыве


async def broadcast_end(day, time):
    await radioboss.radioboss_api(cmd='setvol 0')  # выключить музло на паре
    await perezaklad(day, time)


async def start_up():
    await BOT.send_message(ADMINS_CHAT_ID, "Ребутнулся!")


async def perezaklad(day, time):
    tracks = files.get_downloaded_tracks(day, time)
    for track_path in tracks:
        if not (tag := await radioboss.read_track_additional_info(track_path)):
            continue

        with open(str(track_path), 'rb') as file:
            try:
                await BOT.send_audio(tag['id'], file, caption=consts.texts.ORDER_PEREZAKLAD,
                                     reply_markup=await keyboards.order_choose_day())
            except Exception as ex:
                logging.info(f"perezaklad send msg: {ex}")
                logging.warning(f"pls pls add exception {type(ex)}{ex} in except")

        await asyncio.sleep(3)
