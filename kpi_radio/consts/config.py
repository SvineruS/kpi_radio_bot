import asyncio
import logging
from os import getenv
from pathlib import Path

import aiohttp
import matplotlib
from aiogram import Bot
from dotenv import load_dotenv

matplotlib.use('agg')  # что бы не устанавливать tkinter

PATH_ROOT = Path(__file__).parent.parent.parent
PATH_STUFF = Path('/stuff')
PATH_LOG = PATH_STUFF / 'debug.log'

load_dotenv(dotenv_path=PATH_STUFF / '.env')

# noinspection PyArgumentList
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)-8s [%(filename)s:%(lineno)d > %(funcName)s] \t  %(name)-8s %(message)s',
    datefmt='%d.%m %H:%M:%S',
    handlers=[logging.FileHandler(PATH_LOG), logging.StreamHandler()]
)

IS_TEST_ENV = getenv("ENV_TYPE") == 'TEST'

#

TOKEN = getenv("TOKEN")
TOKEN_TEST = getenv("TOKEN_TEST")

ADMINS_CHAT_ID = int(getenv("ADMINS_CHAT_ID"))  # Чат с модерами
HISTORY_CHAT_ID = int(getenv("HISTORY_CHAT_ID"))  # Канал истории

#

MOPIDY_URL = getenv("MOPIDY_URL")

#

HOST = getenv("HOST")
PORT = int(getenv("PORT"))  # port for internal server

WEBHOOK_URL = f"https://{HOST}/webhook"
#

BOT = Bot(token=TOKEN, parse_mode='HTML')
LOOP = asyncio.get_event_loop()
AIOHTTP_SESSION: aiohttp.ClientSession


async def _make_aiohttp_session():
    global AIOHTTP_SESSION
    AIOHTTP_SESSION = aiohttp.ClientSession(loop=LOOP)

LOOP.run_until_complete(_make_aiohttp_session())
