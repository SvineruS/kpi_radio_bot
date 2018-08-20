from music_api import radioboss_api
from time import strptime, mktime
from datetime import datetime
from bot_utils import get_break_num
from json import dumps


def get(date):
    date = datetime.fromtimestamp(int(date))
    playback = radioboss_api(action='getlastplayed')
    if not playback:
        return
    answer = []
    break_num_old = 0
    for track in playback:
        track_datetime = datetime.fromtimestamp(mktime(strptime(track.attrib['STARTTIME'], '%Y-%m-%d %H:%M:%S')))
        if track_datetime.date() < date.date():
            continue
        if track_datetime.date() > date.date():
            break

        break_num_curr = get_break_num(track_datetime)
        if break_num_curr != 0 and break_num_curr != break_num_old:
            break_num_old = break_num_curr

        time_start = mktime(track_datetime.timetuple())
        time_stop = strptime(track.attrib['DURATION'], '%M:%S')
        time_stop = time_start + (time_stop.tm_min*60+time_stop.tm_sec)

        if not track.attrib['ARTIST'] and not track.attrib['TITLE']:
            track.attrib['TITLE'] = track.attrib['CASTTITLE']

        answer.append({
            'artist': track.attrib['ARTIST'],
            'title': track.attrib['TITLE'],
            'time_start': time_start,
            'time_stop': time_stop,
            'para_num': break_num_old if break_num_curr == 0 else break_num_curr
        })

    answer = dumps(answer)
    return answer
