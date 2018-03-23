# -*- coding: utf-8 -*-

import pymongo
from passwords import *

client = pymongo.MongoClient(DB_URL)

db = client.get_database()["kpiradio"]
