from time import time

from motor import motor_asyncio

from config import DB_URL

client = motor_asyncio.AsyncIOMotorClient(DB_URL, retryWrites=False)
db = client.get_database()["kpiradio"]


async def add(id_):
    if not await db.find_one({'usr': id_}):
        await db.insert_one({'usr': id_})


async def ban_get(id_):
    user = await db.find_one({'usr': id_})
    if not user or 'ban' not in user:
        return False
    ban_time = user['ban']
    if ban_time < time():
        return False
    return ban_time


async def ban_set(id_, time_):
    ban_time = time() + time_ * 60
    await db.update_one({'usr': id_}, {'$set': {'ban': ban_time}}, upsert=True)


async def notification_get(id_):
    user = await db.find_one({'usr': id_})
    if not user or 'notification_mute' not in user:
        return False
    return user['notification_mute']


async def notification_set(id_, status_):
    await db.update_one({'usr': id_}, {'$set': {'notification_mute': status_}}, upsert=True)
