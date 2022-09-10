from aiohttp import web

from bot import bot
from consts import config
from main import server, events


def start():
    on_startup = [lambda _: events.STARTUP_EVENT()]
    on_shutdown = [lambda _: events.SHUTDOWN_EVENT()]

    if config.IS_TEST_ENV:
        from utils import DateTime
        # DateTime.fake(2021, 1, 6, 10, 15, 0)
        events.STARTUP_EVENT.register(lambda: events.ETHER_BEGIN_EVENT.notify(2, 0))
        bot.start_longpoll(on_startup=on_startup, on_shutdown=on_shutdown)
        # start_server(on_startup=on_startup, on_shutdown=on_shutdown, port=8080)
    else:
        on_startup.append(lambda _: bot.set_webhook(config.WEBHOOK_URL))
        start_server(on_startup=on_startup, on_shutdown=on_shutdown)


def start_server(on_startup, on_shutdown, ssl_context=None, port=config.PORT):
    app = bot.get_aiohttp_app()
    app.add_routes(server.ROUTES)
    app.on_startup.extend(on_startup)
    app.on_shutdown.extend(on_shutdown)
    web.run_app(app, host='0.0.0.0', port=port, ssl_context=ssl_context, loop=config.LOOP)
