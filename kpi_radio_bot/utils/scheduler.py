import asyncio

import aioschedule

from consts import broadcast_times
from core import send_live_begin
from utils.files import move_to_archive


async def start():
    aioschedule.every().day.at("23:00").do(move_to_archive_)

    for day_num, day_name in enumerate(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
        for break_num, (break_time_start, _) in broadcast_times[day_num].items():
            getattr(aioschedule.every(), day_name).at(break_time_start).do(send_live_begin, break_num)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)


async def move_to_archive_():  # пиздец
    move_to_archive()
