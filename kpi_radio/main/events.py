"""Обработка ивентов (начало перерыва, заиграл трек, ...)"""

import asyncio

import aioschedule

from consts import config, others
from player import Ether, PlaylistItem, Broadcast
from utils import Event

STARTUP_EVENT = Event('statup')
SHUTDOWN_EVENT = Event('shutdown')

TRACK_BEGIN_EVENT = Event('track_begin')
ORDERS_QUEUE_EMPTY_EVENT = Event('orders_empty')

ETHER_BEGIN_EVENT = Event('ether_begin')
ETHER_END_EVENT = Event('ether_end')

DAY_END_EVENT = Event('day_end')


@TRACK_BEGIN_EVENT.handler
async def track_begin(track: PlaylistItem):
    if not (ether := Ether.now()):
        return

    # трек на входе без TrackInfo, надо спиздить с локального плейлиста, если есть
    if local_track := await Broadcast(ether).mark_played(track.path):
        track = track.add_track_info_(local_track.track_info)
    from bot.handlers_ import utils
    await utils.send_history_track(track)


@ETHER_BEGIN_EVENT.handler
async def ether_begin(day, time):
    from bot.handlers_ import utils
    broadcast = Broadcast(Ether(day, time))
    await broadcast.play()
    await utils.send_ether_begin(time)
    await broadcast.player.set_volume(100)  # включить музло на перерыве


@ETHER_END_EVENT.handler
async def ether_end(*_):
    await Broadcast.player.set_volume(0)  # выключить музло на паре


@STARTUP_EVENT.handler
async def start_up():
    from bot.handlers_ import utils

    await asyncio.sleep(5)  # wait for mopidy
    await Broadcast.player.connect()
    
    asyncio.create_task(start_scheduler())

    if not config.IS_TEST_ENV:
        await utils.send_startup_message()


@SHUTDOWN_EVENT.handler
async def shut_down():
    await Broadcast.player.get_client().disconnect()


@DAY_END_EVENT.handler
async def day_end(day):
    for e in Ether.ALL:
        if e.day == day:
            await Broadcast(e).playlist.clear()


@ORDERS_QUEUE_EMPTY_EVENT.handler
async def orders_queue_empty():
    await Broadcast(Ether.now()).play()


async def start_scheduler():
    def _every(day_name_):
        return getattr(aioschedule.every(), day_name_)

    # for every job need to create new object
    for day_num, day_name in enumerate(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
        for ether_num, (ether_time_start, ether_time_stop) in others.ETHER_TIMES[day_num].items():
            _every(day_name).at(ether_time_stop).do(ETHER_END_EVENT, day_num, ether_num)
            _every(day_name).at(ether_time_start).do(ETHER_BEGIN_EVENT, day_num, ether_num)
        _every(day_name).at("23:00").do(DAY_END_EVENT, day_num)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)
