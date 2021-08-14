from itertools import islice

from aiohttp import web

from music import search_text

ROUTES = web.RouteTableDef()


@ROUTES.get("/gettext/{name}")
async def gettext(request):
    if not (name := request.match_info.get('name')):
        return web.Response(text="Использование: /gettext/имя_песни")
    if not (res := await search_text(name)):
        return web.Response(text="Ошибка поиска")
    title, text = res
    return web.Response(text=f"{title} \n\n{text}")


@ROUTES.get("/history")
async def history_get(request):
    from player import Broadcast
    history = await Broadcast.player.get_history()
    history = [
        {
            'performer': item.performer,
            'title': item.title,
            'start_time': str(item.start_time)
        }
        for item in islice(history, 5)
    ]
    return web.json_response(history)
