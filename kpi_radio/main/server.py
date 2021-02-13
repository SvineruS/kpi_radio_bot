from pathlib import Path

from aiohttp import web

from consts.config import RADIOBOSS_DATA
from music import search_text
from .events import TRACK_BEGIN_EVENT

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
    from player import PlaylistItem
    await TRACK_BEGIN_EVENT.notify(
        PlaylistItem(
            path=Path(args.get('path')),
            performer=args.get('artist'),
            title=args.get('title') or args.get('casttitle'),
            duration=0
        )
    )
    return web.Response(text='ok')


@ROUTES.get("/history")
async def history_get(request):
    # todo send history
    return web.Response(text='WIP')
