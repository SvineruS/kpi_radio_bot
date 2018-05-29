# -*- coding: utf-8 -*-

import pymongo
from passwords import *

client = pymongo.MongoClient(DB_URL)
db = client.get_database()["kpiradio"]


def add(id):
    if db.find_one({'usr': id}) is None:
        db.insert({'usr': id})
