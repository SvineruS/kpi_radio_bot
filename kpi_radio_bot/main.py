import asyncio
import logging
import ssl
import sys
import traceback

from aiogram import types, Dispatcher
from aiohttp import web

import core
from bot_handlers import dp
from config import RADIOBOSS_DATA, WEBHOOK_URL, PORT, SSL_PRIV, Bot, bot, SSL_CERT, WEBHOOK_PATH
from utils import music, scheduler

app = web.Application()
routes = web.RouteTableDef()

logging.basicConfig(filename='debug.log', level=logging.DEBUG)


@routes.get("/gettext/{name}")
async def gettext(request):
    name = request.match_info.get('name')
    if not name:
        return web.Response(text="")
    res = await music.search_text(name)
    if not res:
        return web.Response(text="Ошибка поиска")
    title, text = res
    return web.Response(text=f"{title} \n\n{text}")


@routes.get("/playlist")
async def history_save(request):
    # https://HOST:PORT/playlist?artist=%artist%&title%title%&casttitle=%casttitle%&len=%seconds%&path=%path%&pass=pass
    args = request.rel_url.query
    if args.get('pass') != RADIOBOSS_DATA[2]:
        return web.Response(text='neok')
    fields = {
        'artist': args.get('artist'),
        'title': args.get('title'),
        'casttitle': args.get('casttitle'),
        'path': args.get('path'),
    }
    await core.callbacks.send_history(fields)
    return web.Response(text='ok')


@routes.post(WEBHOOK_PATH)
async def webhook_handle(request):
    update = await request.json()
    update = types.Update(**update)
    Bot.set_current(dp.bot)  # без этого не работает
    Dispatcher.set_current(dp)
    try:
        await dp.process_update(update)
    except Exception:
        traceback.print_exception(*sys.exc_info())

    return web.Response(text='ok')


async def on_startup(_):
    webhook = await bot.get_webhook_info()
    print(await bot.me)
    if webhook.url != WEBHOOK_URL:
        if not webhook.url:
            await bot.delete_webhook()
        await bot.set_webhook(WEBHOOK_URL, certificate=open(SSL_CERT, 'rb'))

    asyncio.ensure_future(scheduler.start())
    await core.callbacks.start_up()


async def on_shutdown(_):
    pass


def start():
    app.add_routes(routes)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.load_cert_chain(SSL_CERT, SSL_PRIV)

    web.run_app(
        app,
        host='0.0.0.0',
        port=PORT,
        ssl_context=context
    )


if __name__ == "__main__":
    start()
