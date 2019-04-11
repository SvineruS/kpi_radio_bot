import pymongo

from config import DB_URL

client = pymongo.MongoClient(DB_URL)
db = client.get_database()["kpiradio"]


def add(id_):
    if db.find_one({'usr': id_}) is None:
        db.insert({'usr': id_})
