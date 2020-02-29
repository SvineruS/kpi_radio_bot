"""Методы для работы с бд
Текущая структура бд:
{
    'usr': id пользователя,
    'ban: timestamp, раньше которого юзер не сможет отправлять заказы
    'notification_mute': если True - не уведомлять юзера о том, что заиграл его трек
}
"""
from datetime import datetime
from time import time
from typing import Union

from motor import motor_asyncio

from config import DB_URL

CLIENT = motor_asyncio.AsyncIOMotorClient(DB_URL, retryWrites=False)
DB = CLIENT.get_database()["kpiradio"]


async def add(id_: int):
    if not await _get_user(id_):
        await DB.insert_one({'usr': id_})


async def ban_get(id_: int) -> Union[bool, datetime]:
    if not (user := await _get_user(id_)) or 'ban' not in user:
        return False
    if user['ban'] < time():
        return False
    return datetime.fromtimestamp(user['ban'])


async def ban_set(id_: int, time_: int):
    ban_time = time() + time_ * 60
    await DB.update_one({'usr': id_}, {'$set': {'ban': ban_time}}, upsert=True)


async def notification_get(id_: int) -> bool:
    if not (user := await _get_user(id_)) or 'notification_mute' not in user:
        return False
    return user['notification_mute']


async def notification_set(id_: int, status_: bool):
    await DB.update_one({'usr': id_}, {'$set': {'notification_mute': status_}}, upsert=True)


async def _get_user(id_: int):
    return await DB.find_one({'usr': id_})
