import ssl

from aiohttp import web

from consts import config
from main import server, events


def start():
    server.APP.on_startup.append(events.start_up)
    server.APP.on_shutdown.append(events.shut_down)

    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.load_cert_chain(config.SSL_CERT, config.SSL_PRIV)

    web.run_app(
        server.APP,
        host='0.0.0.0',
        port=config.PORT,
        ssl_context=context
    )
