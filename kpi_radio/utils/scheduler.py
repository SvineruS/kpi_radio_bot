"""Шедулер. Текущие функции:
- Вызывать day_end каждый день в 23:00
- Вызывать broadcast_begin в начале каждого эфира
- Вызывать broadcast_end в конце каждого эфира
"""

import asyncio

import aioschedule


async def start():
    from consts.others import BROADCAST_TIMES
    from main.events import broadcast_begin, broadcast_end, day_end

    aioschedule.every().day.at("23:00").do(day_end)

    for day_num, day_name in enumerate(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
        for broadcast_num, (broadcast_time_start, broadcast_time_stop) in BROADCAST_TIMES[day_num].items():
            getattr(aioschedule.every(), day_name).at(broadcast_time_start).do(broadcast_begin, day_num, broadcast_num)
            getattr(aioschedule.every(), day_name).at(broadcast_time_stop).do(broadcast_end, day_num, broadcast_num)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)
