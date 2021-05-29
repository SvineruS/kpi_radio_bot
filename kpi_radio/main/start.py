import ssl

from aiohttp import web

from bot import bot
from consts import config
from main import server, events


def start():
    _register_player_backend(config.PLAYER)
    on_startup = [lambda _: events.STARTUP_EVENT()]
    on_shutdown = [lambda _: events.SHUTDOWN_EVENT()]

    if config.IS_TEST_ENV:
        from utils import DateTime
        DateTime.fake(2021, 1, 6, 8, 15, 0)
        # events.STARTUP_EVENT.register(lambda: events.BROADCAST_BEGIN_EVENT.notify(2, 0))
        bot.start_longpoll(on_startup=on_startup, on_shutdown=on_shutdown)
        # start_server(on_startup=on_startup, on_shutdown=on_shutdown, port=8080)
    else:
        on_startup.append(lambda _: bot.set_webhook(config.WEBHOOK_URL, config.SSL_CERT.open('rb')))
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)  # radioboss need ssl v23
        ssl_context.load_cert_chain(config.SSL_CERT, config.SSL_PRIV)
        start_server(on_startup=on_startup, on_shutdown=on_shutdown, ssl_context=ssl_context)


def start_server(on_startup, on_shutdown, ssl_context=None, port=config.PORT):
    app = bot.get_aiohttp_app()
    app.add_routes(server.ROUTES)
    app.on_startup.extend(on_startup)
    app.on_shutdown.extend(on_shutdown)
    web.run_app(app, host='0.0.0.0', port=port, ssl_context=ssl_context)


def _register_player_backend(backend):
    if backend == 'MOPIDY':
        from player.backends.mopidy import PlayerMopidy
        player_ = PlayerMopidy(url=config.MOPIDY_URL)

        async def playback_state_changed(data):
            # state = stopped => плейлист пустой
            if data == {'old_state': 'playing', 'new_state': 'stopped'}:
                await events.ORDERS_QUEUE_EMPTY_EVENT.notify()

        async def track_playback_started(data):
            track = PlayerMopidy.internal_to_playlist_item(data['tl_track'].track)
            await events.TRACK_BEGIN_EVENT.notify(track)

        player_.bind_event("playback_state_changed", playback_state_changed)
        player_.bind_event("track_playback_started", track_playback_started)
        events.STARTUP_EVENT.register(player_.get_client().connect)
        events.SHUTDOWN_EVENT.register(player_.get_client().disconnect)

    elif backend == 'RADIOBOSS':
        from player.backends.radioboss import PlayerRadioboss
        from bot.handlers_ import utils

        player_ = PlayerRadioboss()

        async def move_to_archive(day):
            from player.player_utils import archive
            archive.move_to_archive(day)

        events.BROADCAST_END_EVENT.register(utils.perezaklad)
        events.DAY_END_EVENT.register(move_to_archive)

    else:
        raise ValueError(f"шо за хуйня такая {backend}")

    from player.backends import Backend, db
    local_playlist = db.DBPlaylistProvider

    Backend.register_backends(player_, local_playlist)
