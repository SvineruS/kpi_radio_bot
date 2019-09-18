import json
import logging
import xml.etree.ElementTree as Etree
from datetime import datetime
from typing import Union
from urllib.parse import quote_plus

import aiohttp

import consts
from config import *
from utils import broadcast


async def radioboss_api(**kwargs) -> Union[Etree.Element, bool]:
    url = 'http://{}:{}/?pass={}'.format(*RADIOBOSS_DATA)
    for key in kwargs:
        url += '&{0}={1}'.format(key, quote_plus(str(kwargs[key])))
    t = ''
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.encoding = 'utf-8'
                t = await resp.text()
                if not t:
                    return False
                if t == 'OK':
                    return True
                return Etree.fromstring(t)
    except Exception as e:
        logging.error(f'radioboss: {e} {t} {url}')
        return False


async def get_now():
    playback = await radioboss_api(action='playbackinfo')
    answer = [r'¯\_(ツ)_/¯'] * 3
    if not playback or playback[3].attrib['state'] == 'stop':
        return None
    for i in range(3):
        title = playback[i][0].attrib['CASTTITLE']
        if "setvol" in title:
            continue

        answer.append(title)
    return answer


async def get_next():
    playlist = await get_playlist()
    bn = broadcast.get_broadcast_num()
    if not playlist or bn is False:
        return []

    answer = []

    dt_now = datetime.now()
    time_min = dt_now.time()
    time_max = consts.broadcast_times[dt_now.weekday()][bn][1]
    time_max = datetime.strptime(time_max, '%H:%M').time()

    for track in playlist:
        time_start = track["time_start"].time()
        if time_start < time_min:
            continue
        if time_start > time_max:
            break
        answer.append(track)

    return answer


async def get_playlist():
    answer = []
    playlist = await radioboss_api(action='getplaylist2')
    if not playlist:
        return []

    for track in playlist:
        track = track.attrib
        if not track['STARTTIME']:  # если STARTTIME == "" скорее всего это не песня (либо она стартанет через >=сутки)
            continue

        answer.append({
            'title': track['CASTTITLE'],
            'time_start': datetime.strptime(track['STARTTIME'], '%H:%M:%S'),
            'filename': track['FILENAME'],
            'index': int(track['INDEX']),
            'is_order': str(consts.paths['orders']) in track["FILENAME"]
        })

    return answer


async def get_new_order_pos():
    playlist = await get_next()
    if not playlist:
        return False
    for i in range(len(playlist) - 1, -1, -1):
        track = playlist[i]
        if track["is_order"]:
            if i == len(playlist) - 1:  # если последний трек что успеет проиграть это заказ то пизда, вернем False
                return False
            return playlist[i + 1]  # иначе вернем трек которй будет играть после заказа
    return playlist[0]  # если нету заказов - вернуть самый первый трек в очереди


# todo тут не только инфа отправителя, надо как нить переименовать (зачеркнуто) и переструктурировать
async def write_track_additional_info(path, user_obj, moderation_id):
    tag = {
        'id': user_obj.id,
        'name': user_obj.first_name,
        'moderation_id': moderation_id
    }
    tag = json.dumps(tag)
    await write_comment_tag(path, tag)


async def read_track_additional_info(path):
    tags = await radioboss_api(action='readtag', fn=path)
    tag = tags[0].attrib['Comment']
    try:
        return json.loads(tag)
    except:
        pass


async def clear_track_additional_info(path):
    await write_comment_tag(path, '')


async def write_comment_tag(path, tag):
    tags = await radioboss_api(action='readtag', fn=path)
    tags[0].attrib['Comment'] = tag
    xmlstr = Etree.tostring(tags, encoding='utf8', method='xml').decode('utf-8')
    await radioboss_api(action='writetag', fn=path, data=xmlstr)
