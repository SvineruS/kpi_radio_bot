"""Обработка ивентов (начало перерыва, заиграл трек, ...)"""

import asyncio
import aioschedule

from consts import config, others
from player import Broadcast, PlaylistItem
from utils import Event

STARTUP_EVENT = Event('statup')
SHUTDOWN_EVENT = Event('shutdown')

TRACK_BEGIN_EVENT = Event('track_begin')
ORDERS_QUEUE_EMPTY_EVENT = Event('orders_empty')

BROADCAST_BEGIN_EVENT = Event('broadcast_begin')
BROADCAST_END_EVENT = Event('broadcast_end')

DAY_END_EVENT = Event('day_end')


@TRACK_BEGIN_EVENT.handler
async def track_begin(track: PlaylistItem):
    if not (br := Broadcast.now()):
        return

    # трек на входе без TrackInfo, надо спиздить с локального плейлиста, если есть
    if local_track := await br.mark_played(track.path):
        track = track.add_track_info_(local_track.track_info)
    from bot.handlers_ import utils
    await utils.send_history_track(track)


@BROADCAST_BEGIN_EVENT.handler
async def broadcast_begin(day, time):
    from bot.handlers_ import utils
    await Broadcast(day, time).play()
    await utils.send_broadcast_begin(time)
    await Broadcast.get_player().set_volume(100)  # включить музло на перерыве


@BROADCAST_END_EVENT.handler
async def broadcast_end(*_):
    await Broadcast.get_player().set_volume(0)  # выключить музло на паре


@STARTUP_EVENT.handler
async def start_up():
    from bot.handlers_ import utils

    asyncio.create_task(start_scheduler())

    if not config.IS_TEST_ENV:
        await utils.send_startup_message()


@DAY_END_EVENT.handler
async def day_end(day):
    for b in Broadcast.ALL:
        if b.day == day:
            await b.get_local_playlist().clear()


@ORDERS_QUEUE_EMPTY_EVENT.handler
async def orders_queue_empty():
    await Broadcast.play_from_archive()


async def start_scheduler():

    for day_num, day_name in enumerate(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
        day = getattr(aioschedule.every(), day_name)
        for broadcast_num, (broadcast_time_start, broadcast_time_stop) in others.BROADCAST_TIMES[day_num].items():
            day.at(broadcast_time_start).do(BROADCAST_BEGIN_EVENT, day_num, broadcast_num)
            day.at(broadcast_time_stop).do(BROADCAST_END_EVENT, day_num, broadcast_num)
        day.at("23:00").do(DAY_END_EVENT, day_num)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)
