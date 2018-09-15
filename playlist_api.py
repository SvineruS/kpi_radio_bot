from music_api import radioboss_api
from json import dumps
from datetime import datetime
from bot_utils import get_break_num


def get_prev():
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


def get_next(all=False):
    answer = []

    playlist = radioboss_api(action='getplaylist2')
    if not playlist or \
            len(playlist) < 2 or \
            playlist[0].attrib['CASTTITLE'] == 'stop ':
        return answer

    dt_now = datetime.now()
    time_min = dt_now.time()
    bn = get_break_num()
    if dt_now.weekday() == 6:
        time_max = datetime.strptime(['18:00', '22:00'][bn-1], '%H:%M').time()
    else:
        if bn == 5:
            time_max = datetime.strptime('19:00', '%H:%M').time()
        else:
            m = 10*60+25 + (bn-1)*115
            time_max = datetime(1,1,1, hour=m//60, minute=m%60).time()

    for track in playlist:
        time_start = datetime.strptime(track.attrib['STARTTIME'], '%H:%M:%S').time()
        if not all and not time_min <= time_start <= time_max:
            continue

        answer.append({
            'title': track.attrib['CASTTITLE'],
            'time_start': track.attrib['STARTTIME'],
            'index': track.attrib['INDEX'],
        })

    return answer


def get_now():
    answer = []
    playback = radioboss_api(action='playbackinfo')
    if not playback or \
           playback[3].attrib['state'] == 'stop':
        return answer
    for i in range(3):
        answer.append(playback[i][0].attrib['CASTTITLE'])
    return answer






def move_next(n1, n2):
    playback = radioboss_api(action='move', pos1=n1, pos2=n2)
    print(playback)



def get_duration(s):
    a = list(map(int, s.split(':')))
    return a[0]*60+a[1]


print(get_next())