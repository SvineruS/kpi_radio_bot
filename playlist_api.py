from music_api import radioboss_api
from datetime import datetime
from bot_utils import get_break_num
from pathlib import Path

DB_PATH = Path(__file__).parent / 'Stuff/history.db'


async def prev_get():
    answer = []
    playback = await radioboss_api(action='getlastplayed')
    if not playback:
        return answer

    for i in range(min(5, len(playback))):
        track = playback[i].attrib
        answer.append({
            'time_start': track['STARTTIME'].split(' ')[1],
            'title': track['CASTTITLE']
        })

    return answer


async def next_get():
    answer = []

    playlist = await radioboss_api(action='getplaylist2')
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
        if i >= 5:
            break
        time_start = datetime.strptime(track.attrib['STARTTIME'], '%H:%M:%S').time()
        if not time_min < time_start < time_max:
            continue

        item = {
            'title': track.attrib['CASTTITLE'],
            'time_start': track.attrib['STARTTIME']
        }
        i += 1
            
        answer.append(item)  

    return answer


async def now_get():
    answer = []
    playback = await radioboss_api(action='playbackinfo')
    if not playback or \
           playback[3].attrib['state'] == 'stop':
        return answer
    for i in range(3):
        answer.append(playback[i][0].attrib['CASTTITLE'])
    return answer


async def next_move(n1, n2):
    playback = await radioboss_api(action='move', pos1=n1, pos2=n2)
    print(playback)

