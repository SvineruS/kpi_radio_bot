import logging
from os import getenv
from pathlib import Path

import aiohttp
from aiogram import Bot
from dotenv import load_dotenv

PATH_SELF = Path(__file__).parent.parent
PATH_STUFF = PATH_SELF / 'stuff'
PATH_LOG = PATH_STUFF / 'debug.log'

load_dotenv(dotenv_path=PATH_STUFF / '.env')
logging.basicConfig(level=logging.INFO,
                    handlers=[logging.FileHandler(PATH_LOG), logging.StreamHandler()])

IS_TEST_ENV = bool(getenv("IS_TEST_ENV"))

TOKEN = getenv("TOKEN")
TOKEN_TEST = getenv("TOKEN_TEST")

ADMINS_CHAT_ID = int(getenv("ADMINS_CHAT_ID"))  # Чат с модерами
HISTORY_CHAT_ID = int(getenv("HISTORY_CHAT_ID"))  # Чат истории

# ip, port, password.   Узнать в радиобоссе->настройки->api
RADIOBOSS_DATA = (
    getenv("RADIOBOSS_IP"),
    int(getenv("RADIOBOSS_PORT")),
    getenv("RADIOBOSS_PASSWORD")
)

DB_URL = getenv("DB_URL")

HOST = getenv("HOST")
PORT = int(getenv("PORT"))  # 443, 80, 88 or 8443 (port need to be 'open')

SSL_CERT = PATH_STUFF / 'webhook_cert.pem'
SSL_PRIV = PATH_STUFF / 'webhook_pkey.pem'

WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"https://{HOST}:{PORT}{WEBHOOK_PATH}"

if IS_TEST_ENV:
    TOKEN = TOKEN_TEST

BOT = Bot(token=TOKEN, parse_mode='HTML')
AIOHTTP_SESSION = aiohttp.ClientSession()
