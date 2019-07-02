import asyncio
import aioschedule
from core import send_live_begin
from bot_utils import delete_old_orders
from consts import broadcast_times


async def start():
    aioschedule.every().day.at("23:00").do(delete_old_orders_)

    for day_num, day_name in enumerate(('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')):
        for break_num, (break_time_start, _) in broadcast_times[day_num].items():
            getattr(aioschedule.every(), day_name).at(break_time_start).do(send_live_begin, break_num)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)


async def delete_old_orders_():  # пиздец
    delete_old_orders()
