from aiogram import Dispatcher
from aiogram.dispatcher.webhook import get_new_configured_app
from aiogram.utils import executor

from bot.bot_utils import bind_filters
from consts.config import BOT
from .handlers import register_handlers

DP = Dispatcher(BOT)
bind_filters(DP)
register_handlers(DP)


async def set_webhook(url, cert):
    if (await BOT.get_webhook_info()).url != url:
        await BOT.set_webhook(url, certificate=cert)


def start_longpoll(**kwargs):
    executor.start_polling(DP, skip_updates=True, **kwargs)


def get_aiohttp_app():
    return get_new_configured_app(DP)
