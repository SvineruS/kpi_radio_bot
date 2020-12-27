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
PATH_STUFF = PATH_ROOT / 'stuff'
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

TOKEN = getenv("TOKEN")
TOKEN_TEST = getenv("TOKEN_TEST")

ADMINS_CHAT_ID = int(getenv("ADMINS_CHAT_ID"))  # Чат с модерами
HISTORY_CHAT_ID = int(getenv("HISTORY_CHAT_ID"))  # Канал истории


# ip, port, password.   Узнать в радиобоссе->настройки->api
RADIOBOSS_DATA = (
    getenv("RADIOBOSS_IP"),
    int(getenv("RADIOBOSS_PORT")),
    getenv("RADIOBOSS_PASSWORD")
)

HOST = getenv("HOST")
PORT = int(getenv("PORT"))  # 443, 80, 88 or 8443 (port need to be 'open')

SSL_CERT = PATH_STUFF / 'webhook_cert.pem'
SSL_PRIV = PATH_STUFF / 'webhook_pkey.pem'

WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"https://{HOST}:{PORT}{WEBHOOK_PATH}"

if IS_TEST_ENV:
    TOKEN = TOKEN_TEST

BOT = Bot(token=TOKEN, parse_mode='HTML')
LOOP = asyncio.get_event_loop()
AIOHTTP_SESSION: aiohttp.ClientSession


async def _make_aiohttp_session():
    global AIOHTTP_SESSION
    AIOHTTP_SESSION = aiohttp.ClientSession(loop=LOOP)

LOOP.run_until_complete(_make_aiohttp_session())
