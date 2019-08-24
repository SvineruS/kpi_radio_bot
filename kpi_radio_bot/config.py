from pathlib import Path
from aiogram import Bot

PATH_SELF = Path(__file__).parent.parent
PATH_STUFF = PATH_SELF / 'stuff'

TOKEN = 'TOKEN_PROD'

# Чат с модерами
ADMINS_CHAT_ID = -100123456789

# Чат истории
HISTORY_CHAT_ID = -100123456789

# ip, port, password.   Узнать в радиобоссе->настройки->api
RADIOBOSS_DATA = ('127.0.0.1', 9000, '1')

DB_URL = "mongodb://MONGODBAUTHINFORMATION"

HOST = '0.0.0.0'
PORT = 443  # 443, 80, 88 or 8443 (port need to be 'open')

SSL_CERT = PATH_STUFF / 'webhook_cert.pem'
SSL_PRIV = PATH_STUFF / 'webhook_pkey.pem'

WEBHOOK_PATH = '/webhook'
WEBHOOK_URL = f"https://{HOST}:{PORT}{WEBHOOK_PATH}"

bot = Bot(token=TOKEN, parse_mode='HTML')
