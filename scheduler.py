import asyncio
import aioschedule
from datetime import datetime
from bot_utils import get_music_path
from shutil import move, rmtree
from os import makedirs
from core import send_live_begin


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


def delete_old_orders():
    wd = datetime.now().weekday()
    src = str(get_music_path(wd, False, False))
    dst = str(get_music_path(wd, False, True).parent.parent / 'Архив')
    try:
        move(src, dst)
    except:
        pass
    try:
        rmtree(src)
    except:
        pass
    for i in range(1, 6):
        src = str(get_music_path(wd, i, False))
        try:
            makedirs(src)
        except:
            pass
