from motor import motor_asyncio

from consts.config import DB_URL

CLIENT = motor_asyncio.AsyncIOMotorClient(DB_URL, retryWrites=False)
DB = CLIENT.get_database()
