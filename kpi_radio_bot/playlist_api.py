import xml.etree.ElementTree as Etree
from datetime import datetime
from base64 import b64decode, b64encode
from bot_utils import get_break_num, get_user_name
from music_api import radioboss_api


async def get_prev():
    answer = []
    playback = await get_playlist()
    if not playback:
        return answer

    return playback[:min(5, len(playback))]


async def get_playlist():
    answer = []
    playlist = await radioboss_api(action='getplaylist2')
    if not playlist or len(playlist) < 2 or playlist[0].attrib['CASTTITLE'] == 'stop ':
        return answer
    for track in playlist:
        if not track.attrib['STARTTIME']:  # в конце эфира STARTTIME=""
            continue

        item = {
            'title': track.attrib['CASTTITLE'],
            'time_start': datetime.strptime(track.attrib['STARTTIME'], '%H:%M:%S'),
            'filename': track.attrib['FILENAME'],
            'index': int(track.attrib['INDEX']),
        }
        try:
            item['time_end'] = item['time_start'] + datetime.strptime(track.attrib['DURATION'], '%M:%S')
        except:
            item['time_end'] = item['time_start']

        answer.append(item)
    return answer


async def get_next():
    answer = []
    playlist = await get_playlist()

    dt_now = datetime.now()
    time_min = dt_now.time()
    bn = get_break_num()
    if bn == -1:
        time_max = datetime.strptime(['18:00', '22:00'][bn - 1], '%H:%M').time()
    elif bn == 5:
        time_max = datetime.strptime('22:00', '%H:%M').time()
    else:
        m = 10 * 60 + 25 + (bn - 1) * 115
        time_max = datetime(1, 1, 1, hour=m // 60, minute=m % 60).time()

    i = 0
    for track in playlist:
        if i >= 5:
            break
        time_start = track["time_start"].time()
        if not time_min < time_start < time_max:
            continue
        i += 1
        answer.append(track)
    return answer


async def get_now():
    answer = []
    playback = await radioboss_api(action='playbackinfo')
    if not playback or playback[3].attrib['state'] == 'stop':
        return answer
    for i in range(3):
        answer.append(playback[i][0].attrib['CASTTITLE'])
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
