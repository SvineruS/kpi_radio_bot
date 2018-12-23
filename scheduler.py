import schedule
from datetime import datetime
from bot_utils import get_music_path
from shutil import move, rmtree
from time import sleep
from os import makedirs
from bot import send_live_begin



def start():
    schedule.every().day.at("23:00").do(delete_old_orders)

    for index, time in enumerate(('10:05', '12:00', '13:55', '15:50', '17:50')):
        if index == 4:
            index = 5  # потому шо везде вечер это 5 а тут 4
        schedule.every().monday.at(time).do(lambda time_=index: send_live_begin(time_))
        schedule.every().tuesday.at(time).do(lambda time_=index: send_live_begin(time_))
        schedule.every().wednesday.at(time).do(lambda time_=index: send_live_begin(time_))
        schedule.every().thursday.at(time).do(lambda time_=index: send_live_begin(time_))
        schedule.every().friday.at(time).do(lambda time_=index: send_live_begin(time_))
        schedule.every().saturday.at(time).do(lambda time_=index: send_live_begin(time_))

    schedule.every().sunday.at('10:00').do(lambda: send_live_begin(-1))
    schedule.every().sunday.at('18:00').do(lambda: send_live_begin(5))

    while True:
        schedule.run_pending()
        sleep(1)


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
