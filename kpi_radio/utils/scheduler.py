"""Шедулер. Текущие функции:
- Вызывать day_end каждый день в 23:00
- Вызывать broadcast_begin в начале каждого эфира
- Вызывать broadcast_end в конце каждого эфира
"""

import asyncio

import aioschedule


async def start():
    from consts.others import BROADCAST_TIMES
    from main.events import BROADCAST_BEGIN_EVENT, BROADCAST_END_EVENT, DAY_END_EVENT

    aioschedule.every().day.at("23:00").do(DAY_END_EVENT)

    for day_num, day_name in enumerate(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
        for broadcast_num, (broadcast_time_start, broadcast_time_stop) in BROADCAST_TIMES[day_num].items():
            day = getattr(aioschedule.every(), day_name)
            day.at(broadcast_time_start).do(BROADCAST_BEGIN_EVENT, day_num, broadcast_num)
            day.at(broadcast_time_stop).do(BROADCAST_END_EVENT, day_num, broadcast_num)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)
