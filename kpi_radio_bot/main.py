import asyncio
import logging
import ssl
import sys
import traceback

from aiogram import types, Dispatcher, Bot
from aiohttp import web

import config
import core
from bot_handlers import DP
from utils import music, scheduler

APP = web.Application()
ROUTES = web.RouteTableDef()


@ROUTES.get("/gettext/{name}")
async def gettext(request):
    name = request.match_info.get('name')
    if not name:
        return web.Response(text="Использование: /gettext/имя_песни")
    res = await music.search_text(name)
    if not res:
        return web.Response(text="Ошибка поиска")
    title, text = res
    return web.Response(text=f"{title} \n\n{text}")


@ROUTES.get("/playlist")
async def history_save(request):
    # https://HOST:PORT/playlist?artist=%artist%&title%title%&casttitle=%casttitle%&len=%seconds%&path=%path%&pass=pass
    args = request.rel_url.query
    if args.get('pass') != config.RADIOBOSS_DATA[2]:
        return web.Response(text='neok')
    fields = {
        'artist': args.get('artist'),
        'title': args.get('title'),
        'casttitle': args.get('casttitle'),
        'path': args.get('path'),
    }
    await core.callbacks.send_history(fields)
    return web.Response(text='ok')


@ROUTES.post(config.WEBHOOK_PATH)
async def webhook_handle(request):
    update = await request.json()
    update = types.Update(**update)
    Bot.set_current(DP.bot)  # без этого не работает
    Dispatcher.set_current(DP)
    try:
        await DP.process_update(update)
    except Exception as ex:
        traceback.print_exception(*sys.exc_info())
        logging.warning(f"pls add exception {ex} in except")

    return web.Response(text='ok')


async def on_startup(_):
    webhook = await config.BOT.get_webhook_info()
    print(await config.BOT.me)
    if webhook.url != config.WEBHOOK_URL:
        if not webhook.url:
            await config.BOT.delete_webhook()
        await config.BOT.set_webhook(config.WEBHOOK_URL, certificate=open(config.SSL_CERT, 'rb'))

    asyncio.ensure_future(scheduler.start())
    await core.callbacks.start_up()


async def on_shutdown(_):
    pass


def start():
    APP.add_routes(ROUTES)

    APP.on_startup.append(on_startup)
    APP.on_shutdown.append(on_shutdown)

    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.load_cert_chain(config.SSL_CERT, config.SSL_PRIV)

    web.run_app(
        APP,
        host='0.0.0.0',
        port=config.PORT,
        ssl_context=context
    )


if __name__ == "__main__":
    start()
