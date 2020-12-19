import asyncio

from aiogram import types, Bot, Dispatcher
from aiohttp import web

from bot.handlers import DP
from consts.config import WEBHOOK_PATH, RADIOBOSS_DATA
from music import search_text
from utils import events

APP = web.Application()
ROUTES = web.RouteTableDef()


@ROUTES.get("/gettext/{name}")
async def gettext(request):
    if not (name := request.match_info.get('name')):
        return web.Response(text="Использование: /gettext/имя_песни")
    if not (res := await search_text(name)):
        return web.Response(text="Ошибка поиска")
    title, text = res
    return web.Response(text=f"{title} \n\n{text}")


@ROUTES.get("/playlist")
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
    await events.send_history(fields)
    return web.Response(text='ok')


@ROUTES.post(WEBHOOK_PATH)
async def webhook_handle(request):
    update = await request.json()
    update = types.Update(**update)

    Bot.set_current(DP.bot)  # без этого не работает
    Dispatcher.set_current(DP)
    asyncio.create_task(DP.process_update(update))

    return web.Response(text='ok')


APP.add_routes(ROUTES)
