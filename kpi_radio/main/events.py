"""Обработка ивентов (начало перерыва, заиграл трек, ...)"""

import asyncio

from bot.handlers_ import utils
from consts import config
from player import Broadcast, Player
from player.player import PlayerMopidy
from player.player_utils import files, track_info
from utils import scheduler


async def track_begin(path, artist, title):
    if Broadcast.is_broadcast_right_now():  # кидать только во время перерыва
        await utils.send_history_track(path, artist, title)


async def track_end_mopidy(_):
    # если нет следующей песни - ставим с архива
    if await PlayerMopidy.get_state() != 'stopped':
        return
    if not (track := files.get_random_from_archive()):
        return
    track = (await Player.add_track(track, -1))[0]
    await Player.play(tlid=track.tlid)


async def broadcast_begin(day, time):
    await Broadcast(day, time).play()
    await utils.send_broadcast_begin(time)
    await Player.set_volume(100)  # включить музло на перерыве


async def broadcast_end(day, time):
    await Player.set_volume(0)  # выключить музло на паре
    await _perezaklad(day, time)


async def day_end():
    files.move_to_archive()


async def start_up(_):
    asyncio.create_task(scheduler.start())

    if config.PLAYER == 'MOPIDY':
        await PlayerMopidy.get_client().connect()
        PlayerMopidy.bind_event("track_playback_ended", track_end_mopidy)

    if not config.IS_TEST_ENV:
        await utils.send_startup_message()


async def shut_down(_):
    if config.PLAYER == 'MOPIDY':
        await PlayerMopidy.get_client().disconnect()


async def _perezaklad(day, time):
    tracks = files.get_downloaded_tracks(Broadcast(day, time).path)
    for track_path in tracks:
        if tag := await track_info.read(track_path):
            await utils.send_perezaklad(tag['id'], track_path)
            await asyncio.sleep(3)
