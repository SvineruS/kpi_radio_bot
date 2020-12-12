"""Шедулер. Текущие функции:
- В 23:00 перемещать треки с папки текущего дня в папку архив
- Вызывать broadcast_begin в начале каждого эфира
- Вызывать broadcast_end в конце каждого эфира
"""

import asyncio

import aioschedule

from player.files import move_to_archive
from consts.others import BROADCAST_TIMES
from bot.handlers_.events import broadcast_begin, broadcast_end


async def start():
    aioschedule.every().day.at("23:00").do(move_to_archive_)

    for day_num, day_name in enumerate(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
        for broadcast_num, (broadcast_time_start, broadcast_time_stop) in BROADCAST_TIMES[day_num].items():
            getattr(aioschedule.every(), day_name).at(broadcast_time_start).do(broadcast_begin, broadcast_num)
            getattr(aioschedule.every(), day_name).at(broadcast_time_stop).do(broadcast_end, day_num, broadcast_num)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)


async def move_to_archive_():  # пиздец
    move_to_archive()
