import logging
import asyncio

import consts
import keyboards
from config import *
from utils import other, radioboss, broadcast, db


async def send_history(fields):
    if str(consts.paths['archive']) in fields['path']:  # песни с архива не играют на политехнической, только на ютубе
        return

    if not fields['artist'] and not fields['title']:
        fields['title'] = fields['casttitle']

    sender_name = ''
    tag = await radioboss.read_track_additional_info(fields['path'])
    await radioboss.clear_track_additional_info(fields['path'])  # Очистить тег что бы уведомление не пришло еще раз

    if tag:
        sender_name = consts.TextConstants.HISTORY_TITLE.format(other.get_user_name_(tag['id'], tag['name']))
        if not db.notification_get(tag['id']):
            await bot.send_message(tag['id'], consts.TextConstants.ORDER_PLAYING.format(fields['casttitle']))
        await bot.edit_message_reply_markup(ADMINS_CHAT_ID, tag['moderation_id'], reply_markup=None)

    with open(fields['path'], 'rb') as f:
        await bot.send_audio(HISTORY_CHAT_ID, f, sender_name, performer=fields['artist'], title=fields['title'])


async def broadcast_begin(time):
    await bot.send_message(HISTORY_CHAT_ID, broadcast.get_broadcast_name(time))


async def broadcast_end(day, time):
    tracks = broadcast.get_broadcast_path(day, time).iterdir()
    for track_path in tracks:
        tag = await radioboss.read_track_additional_info(track_path)
        if not tag:
            continue
        with open(str(track_path), 'rb') as file:
            try:
                await bot.send_audio(tag['id'], file, caption=consts.TextConstants.ORDER_PEREZAKLAD,
                                     reply_markup=await keyboards.choice_day())
            except Exception as e:
                logging.info(f"perezaklad: {e}")

        await asyncio.sleep(3)
