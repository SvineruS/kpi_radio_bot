from time import time, mktime
from datetime import datetime
from bot_utils import get_break_num
from json import dumps, loads
from config import *
import os.path


DB_PATH = os.path.join(os.path.dirname(__file__), 'history.db')


def html():
    f = open('Stuff/history.html', encoding='UTF-8')
    m = f.read()
    f.close()
    return m


def get(date):
    date = datetime.fromtimestamp(int(date))
    key = date2stamp(date)
    history = read()
    answer = []

    if key not in history:
        return dumps(answer)

    break_num_old = 0
    for track in history[key]:
        break_num_curr = get_break_num(datetime.fromtimestamp(track['time_start']))
        if break_num_curr != 0 and break_num_curr != break_num_old:
            break_num_old = break_num_curr

        if not track.attrib['ARTIST'] and not track.attrib['TITLE']:
            track.attrib['TITLE'] = track.attrib['CASTTITLE']

        answer.append({
            'artist': track['artist'],
            'title': track['title'],
            'time_start': track['time_start'],
            'time_stop': track['time_stop'],
            'para_num': break_num_old if break_num_curr == 0 else break_num_curr
        })

    answer = dumps(answer)
    return answer


def save(args):
    if args.get('pass') != str(list(RADIOBOSS_DATA)[2]):
        return 'wrong pass'
    obj = {
        'artist': args.get('artist'),
        'title': args.get('title'),
        'casttitle': args.get('casttitle'),
        'time_start': time(),
        'time_stop': time() + int(args.get('len')),
        'path': args.get('path'),
    }
    key = date2stamp(datetime.today())
    history = read()
    if key not in history:
        history[key] = []
    history[key].append(obj)
    write(history)


def date2stamp(date):
    return int(mktime(date.date().timeturple()))


def write(history):
    history = dumps(history)
    f = open(DB_PATH, 'w')
    f.write(history)
    f.close()


def read():
    try:
        f = open(DB_PATH, 'r')
    except:
        write({})
        return {}
    history = loads(f.read())
    f.close()
    return history