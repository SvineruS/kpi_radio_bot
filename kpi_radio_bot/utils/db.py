import pymongo
from time import time
from config import DB_URL

client = pymongo.MongoClient(DB_URL)
db = client.get_database()["kpiradio"]


def add(id_):
    if not db.find_one({'usr': id_}):
        db.insert({'usr': id_})


def ban_get(id_):
    user = db.find_one({'usr': id_})
    if not user or 'ban' not in user:
        return False
    ban_time = user['ban']
    if ban_time < time():
        return False
    return ban_time


def ban_set(id_, time_):
    ban_time = time() + time_ * 60
    db.update_one({'usr': id_}, {'$set': {'ban': ban_time}}, upsert=True)


def notification_get(id_):
    user = db.find_one({'usr': id_})
    if not user or 'notification_mute' not in user:
        return False
    return user['notification_mute']


def notification_set(id_, status_):
    db.update_one({'usr': id_}, {'$set': {'notification_mute': status_}}, upsert=True)
