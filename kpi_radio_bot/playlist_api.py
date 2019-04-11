import xml.etree.ElementTree as Etree
from base64 import b64decode, b64encode
from datetime import datetime

import consts
from bot_utils import get_break_num, get_user_name
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
    bn = get_break_num()
    if not playlist or bn is False:
        return []

    dt_now = datetime.now()
    time_min = dt_now.time()
    time_max = consts.broadcast_times['sunday' if dt_now.day == 6 else 'elseday'][bn][1]
    time_max = datetime.strptime(time_max, '%H:%M').time()

    for track in playlist:
        if len(answer) >= 5:
            break
        time_start = track["time_start"].time()
        if time_min < time_start < time_max:
            answer.append(track)

    return answer


async def get_playlist():
    answer = []
    playlist = await radioboss_api(action='getplaylist2')
    if not playlist or len(playlist) < 2 or playlist[0].attrib['CASTTITLE'] == 'stop ':   # todo тут точно с пробелом?
        return []

    for track in playlist:
        track = track.attrib
        if not track['STARTTIME']:  # в конце эфира STARTTIME=""
            continue

        item = {
            'title': track['CASTTITLE'],
            'time_start': datetime.strptime(track['STARTTIME'], '%H:%M:%S'),
            'filename': track['FILENAME'],
            'index': int(track['INDEX']),
        }
        answer.append(item)

    return answer


async def get_suggestion_data() -> tuple:
    index = -2  # Поставить следующим
    wait_time = 0
    last_order = None
    playlist = await get_playlist()
    dt_now = datetime.now()
    time_min = dt_now.time()

    for track in playlist:
        if "Заказы" in track["filename"] and track["time_start"].time() > time_min:
            last_order = track

    if last_order:
        wait_time = int(str(last_order['time_end'] - dt_now).split(":")[1])
        index = last_order['index'] + 1

    return index, wait_time


async def write_sender_tag(path, user_obj):
    tags = await radioboss_api(action='readtag', fn=path)
    name = get_user_name(user_obj)
    name = b64encode(name.encode('utf-8')).decode('utf-8')
    tags[0].attrib['Comment'] = name
    xmlstr = Etree.tostring(tags, encoding='utf8', method='xml').decode('utf-8')
    await radioboss_api(action='writetag', fn=path, data=xmlstr)


async def read_sender_tag(path):
    tags = await radioboss_api(action='readtag', fn=path)
    name = tags[0].attrib['Comment']
    try:
        name = b64decode(name).decode('utf-8')
    except:
        return False
    return name
