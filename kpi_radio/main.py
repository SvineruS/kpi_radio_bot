import asyncio
import ssl

from aiohttp import web

from consts import config
from utils import scheduler, events, server


async def on_startup(_):
    if (await config.BOT.get_webhook_info()).url != config.WEBHOOK_URL:
        await config.BOT.set_webhook(config.WEBHOOK_URL, certificate=config.SSL_CERT.open('rb'))

    asyncio.create_task(scheduler.start())
    await events.start_up()


async def on_shutdown(_):
    await events.shut_down()


def start():
    server.APP.on_startup.append(on_startup)
    server.APP.on_shutdown.append(on_shutdown)

    context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
    context.load_cert_chain(config.SSL_CERT, config.SSL_PRIV)

    web.run_app(
        server.APP,
        host='0.0.0.0',
        port=config.PORT,
        ssl_context=context
    )


if __name__ == "__main__":
    start()
