from music_api import radioboss_api
from time import strptime, mktime
from datetime import datetime
from bot_utils import get_break_num
from json import dumps


def get(date):
    date = datetime.fromtimestamp(date)
    playback = radioboss_api(action='getlastplayed')
    if not playback:
        return
    answer = []

    old_num = 0

    for track in playback:
        track_datetime = datetime.fromtimestamp(mktime(strptime(track.attrib['STARTTIME'], '%Y-%m-%d %H:%M:%S')))
        if track_datetime.date() < date.date():
            continue
        if track_datetime.date() > date.date():
            break

        break_num_curr = get_break_num(track_datetime)
        if break_num_curr != 0 and break_num_curr != old_num:
            answer.append({'track': False, 'title': 'newnum' + str(break_num_curr)})
            old_num = break_num_curr

        answer.append({
            'track': track.attrib['CASTTITLE'],
            'time': track_datetime.strftime("%H:%M")
        })

    answer = dumps(answer)
    return answer
