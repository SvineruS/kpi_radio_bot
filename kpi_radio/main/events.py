"""Обработка ивентов (начало перерыва, заиграл трек, ...)"""

import asyncio

from bot.handlers_ import utils
from player import Broadcast, Player
from player.player_utils import files, track_info
from utils import scheduler


async def send_history(fields):
    if Broadcast.is_broadcast_right_now():  # кидать только во время перерыва
        await utils.send_history_track(fields['path'], fields['artist'], fields['title'] or fields['casttitle'])


async def broadcast_begin(time):
    await utils.send_broadcast_begin(time)
    await Player.set_volume(100)  # включить музло на перерыве


async def broadcast_end(day, time):
    await Player.set_volume(0)  # выключить музло на паре
    await _perezaklad(day, time)


async def day_end():
    files.move_to_archive()


async def start_up():
    await utils.set_webhook()
    await utils.send_startup_message()
    asyncio.create_task(scheduler.start())


async def shut_down():
    pass


async def _perezaklad(day, time):
    tracks = files.get_downloaded_tracks(Broadcast(day, time).path)
    for track_path in tracks:
        if tag := await track_info.read(track_path):
            await utils.send_perezaklad(tag['id'], track_path)
            await asyncio.sleep(3)
