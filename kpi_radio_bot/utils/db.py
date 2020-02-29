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

from motor import motor_asyncio

from config import DB_URL

CLIENT = motor_asyncio.AsyncIOMotorClient(DB_URL, retryWrites=False)
DB = CLIENT.get_database()["kpiradio"]


async def add(id_):
    if not await _get_user(id_):
        await DB.insert_one({'usr': id_})


async def ban_get(id_):
    user = await _get_user(id_)
    if not user or 'ban' not in user:
        return False
    ban_time = user['ban']
    if ban_time < time():
        return False

    return datetime.fromtimestamp(ban_time)


async def ban_set(id_, time_):
    ban_time = time() + time_ * 60
    await DB.update_one({'usr': id_}, {'$set': {'ban': ban_time}}, upsert=True)


async def notification_get(id_):
    user = await _get_user(id_)
    if not user or 'notification_mute' not in user:
        return False
    return user['notification_mute']


async def notification_set(id_, status_):
    await DB.update_one({'usr': id_}, {'$set': {'notification_mute': status_}}, upsert=True)


async def _get_user(id_):
    return await DB.find_one({'usr': id_})
