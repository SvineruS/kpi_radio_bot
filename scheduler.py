import schedule
from datetime import datetime
from bot_utils import get_music_path
from shutil import move, rmtree
from time import sleep
from os import makedirs


def start():
    schedule.every().day.at("23:00").do(job)

    while True:
        schedule.run_pending()
        sleep(1)


def job():
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
