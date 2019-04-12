import asyncio
import aioschedule
from core import send_live_begin
from bot_utils import delete_old_orders
from consts import broadcast_times


async def start():
    aioschedule.every().day.at("23:00").do(delete_old_orders_)

    for num, (time, _) in broadcast_times['elseday'].items():
        for day in ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'):
            getattr(aioschedule.every(), day).at(time).do(send_live_begin, num)

    for num, (time, _) in broadcast_times['sunday'].items():
        aioschedule.every().sunday.at(time).do(send_live_begin, num)

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)


async def delete_old_orders_():  # пиздец
    delete_old_orders()
