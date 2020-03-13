"""т
БД кеша треков
Текущая структура таблицы
{
    'api_id': id получаемые с musicless,
    'tg_id: id c телеги
}
"""
from typing import Optional, List, Dict

from consts import config
from utils.db import _connector


if config.IS_TEST_ENV:
    _CACHE = _connector.DB["cache_test"]
else:
    _CACHE = _connector.DB["cache"]


async def update(api_id: str, tg_id: str):
    await _CACHE.update_one({'api_id': api_id}, {'$set': {'tg_id': tg_id}}, upsert=True)


async def get_one(api_id: str) -> Optional[str]:
    if not (res := await _CACHE.find_one({'api_id': api_id})):
        return None
    return res['tg_id']


async def get(api_ids: List[str]) -> Dict[str, str]:
    res = _CACHE.find({'api_id': {"$in": api_ids}})
    res = await res.to_list(length=len(api_ids))
    return {doc['api_id']: doc['tg_id'] for doc in res}


async def delete(api_id: str):
    await _CACHE.delete_one({'api_id': api_id})


async def delete_many(api_ids: List[str]):
    await _CACHE.delete_many({'api_id': {"$in": api_ids}})
