from time import time, mktime
from datetime import datetime
from json import dumps, loads
from config import *
from base64 import b64encode
import os.path


DB_PATH = os.path.join(os.path.dirname(__file__), 'history.db')


def html():
    f = open('Stuff/history.html', encoding='UTF-8')
    m = f.read()
    f.close()
    return m


def get(date):
    key = stamp2key(date)
    history = read()
    answer = []

    if key not in history:
        return dumps(answer)

    for track in history[key]:

        if not track['artist'] and not track['title']:
            track['title'] = track['casttitle']

        answer.append({
            'artist': track['artist'],
            'title': track['title'],
            'time_start': track['time_start'],
            'time_stop': track['time_stop'],
            'para_num': get_break_num(track['time_start']),
            'path': str(track['time_start'])
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
        'time_start': int(time()),
        'time_stop': int(time()) + int(args.get('len')),
        'path': args.get('path'),
    }
    key = stamp2key(time())
    history = read()
    if key not in history:
        history[key] = []
    history[key].append(obj)
    write(history)


def play(path, b64=True):
    key = stamp2key(path)
    history = read()
    for track in history[key]:
        if str(track['time_start']) == path:
            f = open(track['path'], 'rb')
            b = f.read()
            if b64:
                b = 'data:audio/mp3;base64,' + b64encode(b).decode('utf-8')
            f.close()
            return b


def stamp2key(stamp):  # TODO разбиение на файлы по месяцу
    return str(int(mktime(datetime.fromtimestamp(int(stamp)).date().timetuple())))


def write(history):
    history = dumps(history)
    f = open(DB_PATH, 'w')
    f.write(history)
    f.close()


def read():
    try:
        f = open(DB_PATH, 'r')
        history = loads(f.read())
    except:
        write({})
        return {}
    f.close()
    return history


def get_break_num(timestamp):
    time = datetime.fromtimestamp(timestamp)
    day = time.weekday()
    time = time.hour * 60 + time.minute

    if time > 22*60 or time < 10*60+5:
        return 0

    # Воскресенье
    if day == 6:
        if 11*60+15 < time < 18*60:
            return -1
        if time > 18*60:
            return 5

    # Вечерний эфир
    if time > 17*60+50:
        return 5

    # Перерыв
    for i in range(4):
        # 10:05 + пара * i (10:05 - начало 1 перерыва)
        if 0 < time - (10*60+5 + i*115) < 20:
            return i+1

    #Пара
    return 0