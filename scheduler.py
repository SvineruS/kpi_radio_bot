import asyncio
import aioschedule
from core import send_live_begin
from bot_utils import delete_old_orders


async def start():
    aioschedule.every().day.at("23:00").do(delete_old_orders())

    for index, time in enumerate(('7:00', '10:05', '12:00', '13:55', '15:50', '17:50')):
        for day in ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'):
            getattr(aioschedule.every(), day).at(time).do(lambda time_=index: send_live_begin(time_))

    aioschedule.every().sunday.at('10:00').do(lambda: send_live_begin(0))
    aioschedule.every().sunday.at('18:00').do(lambda: send_live_begin(5))

    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(10)
