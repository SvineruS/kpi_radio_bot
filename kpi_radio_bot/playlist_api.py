import xml.etree.ElementTree as Etree
from base64 import b64decode, b64encode
from datetime import datetime

import consts
import bot_utils
from music_api import radioboss_api


async def get_now():
    answer = []
    playback = await radioboss_api(action='playbackinfo')
    if not playback or playback[3].attrib['state'] == 'stop':
        return answer
    for i in range(3):
        answer.append(playback[i][0].attrib['CASTTITLE'])
    return answer


async def get_prev():
    answer = []
    playback = await radioboss_api(action='getlastplayed')
    if not playback:
        return []

    for i in range(min(5, len(playback))):
        track = playback[i].attrib
        answer.append({
            'time_start': datetime.strptime(track['STARTTIME'].split(' ')[1], '%H:%M:%S'),
            'title': track['CASTTITLE']
        })

    return answer


async def get_next():
    answer = []
    playlist = await get_playlist()
    bn = bot_utils.get_break_num()
    if not playlist or bn is False:
        return []

    dt_now = datetime.now()
    time_min = dt_now.time()
    time_max = consts.broadcast_times['sunday' if dt_now.day == 6 else 'elseday'][bn][1]
    time_max = datetime.strptime(time_max, '%H:%M').time()

    for track in playlist:
        time_start = track["time_start"].time()
        if time_min < time_start < time_max:
            answer.append(track)

    return answer


async def get_playlist():
    answer = []
    playlist = await radioboss_api(action='getplaylist2')
    if not playlist or len(playlist) < 2 or playlist[0].attrib['CASTTITLE'] == 'stop':
        return []

    for track in playlist:
        track = track.attrib
        if not track['STARTTIME']:  # в конце эфира STARTTIME == ""
            continue

        answer.append({
            'title': track['CASTTITLE'],
            'time_start': datetime.strptime(track['STARTTIME'], '%H:%M:%S'),
            'filename': track['FILENAME'],
            'index': int(track['INDEX']),
        })

    return answer


async def get_new_order_pos():
    playlist = await get_next()
    for i in range(len(playlist)-1, -1, -1):
        track = playlist[i]
        if "Заказы" in track["filename"]:
            if i == 0:              # если последний трек что успеет проиграть это заказ то пизда, вернем False
                return False
            return playlist[i+1]    # иначе вернем трек которй будет играть после заказа
    return playlist[0]              # если нету заказов - вернуть самый первый трек в очереди


async def write_tag(path, tag):
    tags = await radioboss_api(action='readtag', fn=path)
    tag = b64encode(tag.encode('utf-8')).decode('utf-8')
    tags[0].attrib['Comment'] = tag
    xmlstr = Etree.tostring(tags, encoding='utf8', method='xml').decode('utf-8')
    await radioboss_api(action='writetag', fn=path, data=xmlstr)


async def read_tag(path):
    tags = await radioboss_api(action='readtag', fn=path)
    tag = tags[0].attrib['Comment']
    try:
        tag = b64decode(tag).decode('utf-8')
    except:
        return False
    return tag
