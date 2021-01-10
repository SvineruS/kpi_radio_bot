"""Обработка ивентов (начало перерыва, заиграл трек, ...)"""

import asyncio

from consts import config
from player import Broadcast, Player
from utils import Event

STARTUP_EVENT = Event('statup')
SHUTDOWN_EVENT = Event('shutdown')

TRACK_BEGIN_EVENT = Event('track_begin')
ORDERS_QUEUE_EMPTY_EVENT = Event('orders_empty')

BROADCAST_BEGIN_EVENT = Event('broadcast_begin')
BROADCAST_END_EVENT = Event('broadcast_end')

DAY_END_EVENT = Event('day_end')


@TRACK_BEGIN_EVENT.handler
async def track_begin(path, artist, title):
    from bot.handlers_ import utils
    if Broadcast.is_broadcast_right_now():  # кидать только во время перерыва
        await utils.send_history_track(path, artist, title)


@BROADCAST_BEGIN_EVENT.handler
async def broadcast_begin(day, time):
    from bot.handlers_ import utils
    await Broadcast(day, time).play()
    await utils.send_broadcast_begin(time)
    await Player.set_volume(100)  # включить музло на перерыве


@BROADCAST_END_EVENT.handler
async def broadcast_end(*_):
    await Player.set_volume(0)  # выключить музло на паре


@STARTUP_EVENT.handler
async def start_up():
    from utils import scheduler
    from bot.handlers_ import utils

    asyncio.create_task(scheduler.start())

    if not config.IS_TEST_ENV:
        await utils.send_startup_message()


@DAY_END_EVENT.handler
async def day_end(day):
    for b in Broadcast.ALL:
        if b.day == day:
            await b.get_playlist_provider().clear()


@ORDERS_QUEUE_EMPTY_EVENT.handler
async def orders_queue_empty():
    await Broadcast.play_from_archive()
