import ssl

from aiohttp import web

from bot import bot
from consts import config
from main import server, events


def start():
    on_startup = [events.start_up]
    on_shutdown = [events.shut_down]

    if config.IS_TEST_ENV:
        from utils import DateTime
        DateTime.fake(DateTime(2021, 1, 6, 8, 15, 0))
        on_startup.append(lambda _: events.broadcast_begin(2, 0))
        bot.start_longpoll(on_startup=on_startup, on_shutdown=on_shutdown)
    else:
        on_startup.append(lambda _: bot.set_webhook(config.WEBHOOK_URL, config.SSL_CERT.open('rb')))
        start_webhook(on_startup=on_startup, on_shutdown=on_shutdown)


def start_webhook(on_startup, on_shutdown):
    app = bot.get_aiohttp_app()
    app.add_routes(server.ROUTES)
    app.on_startup.extend(on_startup)
    app.on_shutdown.extend(on_shutdown)

    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(config.SSL_CERT, config.SSL_PRIV)

    web.run_app(app, host='0.0.0.0', port=config.PORT, ssl_context=context)
