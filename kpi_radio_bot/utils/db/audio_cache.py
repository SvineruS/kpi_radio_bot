"""т
БД кеша треков
Текущая структура таблицы
{
    'api_id': id получаемые с musicless,
    'tg_id: id c телеги
}
"""
from typing import Optional

from db import _connector


_CACHE = _connector.DB["cache"]


async def update(api_id: str, tg_id: str):
    await _CACHE.update_one({'api_id': api_id}, {'$set': {'tg_id': tg_id}}, upsert=True)


async def get(api_id: str) -> Optional[str]:
    if not (res := await _CACHE.find_one({'api_id': api_id})):
        return None
    return res['tg_id']
