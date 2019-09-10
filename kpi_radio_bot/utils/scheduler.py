import asyncio

import aioschedule

from consts import broadcast_times
from core import broadcast_begin, broadcast_stop
from utils.files import move_to_archive


async def start():
    aioschedule.every().day.at("23:00").do(move_to_archive_)

    for day_num, day_name in enumerate(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
        for broadcast_num, (broadcast_time_start, broadcast_time_stop) in broadcast_times[day_num].items():
            getattr(aioschedule.every(), day_name).at(broadcast_time_start).do(broadcast_begin, broadcast_num)
            getattr(aioschedule.every(), day_name).at(broadcast_time_stop).do(broadcast_stop, day_num, broadcast_num)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)


async def move_to_archive_():  # пиздец
    move_to_archive()
