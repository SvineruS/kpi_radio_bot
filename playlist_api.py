from music_api import radioboss_api
from datetime import datetime
from bot_utils import get_break_num
from time import time, mktime
from json import dumps, loads
from config import *
from pathlib import Path

DB_PATH = Path(__file__).parent / 'Stuff/history.db'


def prev_get():
    answer = []
    playback = radioboss_api(action='getlastplayed')
    if not playback:
        return answer

    for i in range(min(5, len(playback))):
        track = playback[i].attrib
        answer.append({
            'time_start': track['STARTTIME'].split(' ')[1],
            'title': track['CASTTITLE']
        })

    return answer


def next_get(full=False):
    answer = []

    playlist = radioboss_api(action='getplaylist2')
    if not playlist or len(playlist) < 2 or playlist[0].attrib['CASTTITLE'] == 'stop ':
        return answer

    dt_now = datetime.now()
    time_min = dt_now.time()
    bn = get_break_num()
    if bn == -1:
        time_max = datetime.strptime(['18:00', '22:00'][bn-1], '%H:%M').time()
    elif bn == 5:
        time_max = datetime.strptime('22:00', '%H:%M').time()
    else:
        m = 10*60+25 + (bn-1)*115
        time_max = datetime(1,1,1, hour=m//60, minute=m%60).time()

    i = 0
    for track in playlist:
        if not track.attrib['STARTTIME']:
            continue
        time_start = datetime.strptime(track.attrib['STARTTIME'], '%H:%M:%S').time()
        playable = time_min < time_start < time_max
        
        if not full :
            if not playable:
                continue           
            if i >= 5:
                break
                
        if full:  
            item = {
                'title': track.attrib['CASTTITLE'],
                'index': track.attrib['INDEX'],
                'time_start': time2stamp(datetime.strptime(track.attrib['STARTTIME'], '%H:%M:%S')),
                'playable': playable
            }  
        else:
            item= {
                'title': track.attrib['CASTTITLE'],
                'time_start': track.attrib['STARTTIME']
            }
            i += 1
            
        answer.append(item)  

    return answer



def now_get():
    answer = []
    playback = radioboss_api(action='playbackinfo')
    if not playback or \
           playback[3].attrib['state'] == 'stop':
        return answer
    for i in range(3):
        answer.append(playback[i][0].attrib['CASTTITLE'])
    return answer


def next_move(n1, n2):
    playback = radioboss_api(action='move', pos1=n1, pos2=n2)
    print(playback)


def get_history(date):
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
            'para_num': get_break_num(datetime.fromtimestamp(track['time_start'])),
            'path': str(track['time_start'])
        })

    answer = dumps(answer)
    return answer


def history_save(args):
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


def history_play(path):
    key = stamp2key(path)
    history = read()
    for track in history[key]:
        if str(track['time_start']) == path:
            f = open(track['path'], 'rb')
            b = f.read()
            f.close()
            return b


def stamp2key(stamp):  # TODO разбиение на файлы по месяцу, хранить только этот и предыдущий месяц
    return str(int(mktime(datetime.fromtimestamp(int(stamp)).date().timetuple())))

def time2stamp(time):
    dt = datetime.now().replace(hour=time.hour, minute=time.minute, second=time.second)
    return int(mktime(dt.timetuple()))



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
