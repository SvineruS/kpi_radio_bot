"""
БД Юзеров
Текущая структура таблицы
{
    'usr': id пользователя,
    'ban: timestamp, раньше которого юзер не сможет отправлять заказы
    'notification_mute': если True - не уведомлять юзера о том, что заиграл его трек
}
"""
from datetime import datetime
from time import time
from typing import Optional

from db import _connector
from utils.lru import lru


_users = _connector.DB["kpiradio"]  # todo change to users


async def add(id_: int):
    if not await _get_user(id_):
        await _users.insert_one({'usr': id_})
        _clear_user_cache(id_)


async def ban_get(id_: int) -> Optional[datetime]:
    if not (user := await _get_user(id_)) or 'ban' not in user or user['ban'] < time():
        return None
    return datetime.fromtimestamp(user['ban'])


async def ban_set(id_: int, time_: int):
    ban_time = time() + time_ * 60
    await _users.update_one({'usr': id_}, {'$set': {'ban': ban_time}}, upsert=True)
    _clear_user_cache(id_)


async def notification_get(id_: int) -> bool:
    if not (user := await _get_user(id_)) or 'notification_mute' not in user:
        return False
    return user['notification_mute']


async def notification_set(id_: int, status_: bool):
    await _users.update_one({'usr': id_}, {'$set': {'notification_mute': status_}}, upsert=True)
    _clear_user_cache(id_)


#

@lru(maxsize=1_000, ttl=60 * 60 * 12)
async def _get_user(id_: int):
    return await _users.find_one({'usr': id_})


def _clear_user_cache(id_: int):
    _get_user.cache_del(id_)
