from music_api import radioboss_api
from json import dumps


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


def get_next():
    answer = []

    playlist = radioboss_api(action='getplaylist2')
    if not playlist or \
           len(playlist) < 2 or \
           playlist[0].attrib['CASTTITLE'] == 'stop ':
        return answer

    for track in playlist:
        answer.append({
            'title': track.attrib['CASTTITLE'],
            'time_start': get_duration(track.attrib['DURATION']),
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










def get_duration(s):
    a = list(map(int, s.split(':')))
    return a[0]*60+a[1]


print(get_next())