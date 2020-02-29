import json
import logging
import xml.etree.ElementTree as Etree
from pathlib import Path
from typing import Union
from urllib.parse import quote_plus

import aiohttp
from aiogram.types import User

from config import RADIOBOSS_DATA, AIOHTTP_SESSION


async def setvol(vol: int, fade: int = 500):
    return await _radioboss_api(cmd=f'setvol {vol} {fade}')


async def next():
    return await _radioboss_api(cmd='next')


async def move(pos1: int, pos2: int):
    return await _radioboss_api(action='move', pos1=pos1, pos2=pos2)


async def inserttrack(filename: Path, pos: int):
    return await _radioboss_api(action='inserttrack', filename=filename, pos=pos)


async def delete(pos: int):
    return await _radioboss_api(action='delete', pos=pos)


async def playbackinfo():
    return await _radioboss_api(action='playbackinfo')


async def getplaylist2():
    return await _radioboss_api(action='getplaylist2')


async def readtag(fn: Path):
    return await _radioboss_api(action='readtag', fn=fn)


async def writetag(fn: Path, data: str):
    return await _radioboss_api(action='writetag', fn=fn, data=data)


#


# todo тут не только инфа отправителя, надо как нить переименовать (зачеркнуто) и переструктурировать
async def write_track_additional_info(path: Path, user_obj: User, moderation_id: int):
    tag = {
        'id': user_obj.id,
        'name': user_obj.first_name,
        'moderation_id': moderation_id
    }
    tag = json.dumps(tag)
    await _write_comment_tag(path, tag)


async def read_track_additional_info(path: Path):
    tags = await readtag(path)
    tag = tags[0].attrib['Comment']
    try:
        return json.loads(tag)
    except json.JSONDecodeError:
        logging.warning(f"can't read track comment")


async def clear_track_additional_info(path: Path):
    await _write_comment_tag(path, '')


#

async def _radioboss_api(**kwargs) -> Union[Etree.Element, bool]:
    url = 'http://{}:{}/?pass={}'.format(*RADIOBOSS_DATA)
    for key in kwargs:
        url += '&{0}={1}'.format(key, quote_plus(str(kwargs[key])))
    res = ''
    try:
        async with AIOHTTP_SESSION.get(url) as resp:
            resp.encoding = 'utf-8'
            res = await resp.text()
            if not res:
                return False
            if res == 'OK':
                return True
            return Etree.fromstring(res)

    except aiohttp.ClientConnectionError as ex:
        logging.error(f'radioboss: {ex} {res} {url}')
        return False
    except Exception as ex:
        logging.warning(f"pls pls add exception {type(ex)}{ex}in except")
        return False


async def _write_comment_tag(path: Path, tag: str):
    tags = await readtag(path)
    tags[0].attrib['Comment'] = tag
    xmlstr = Etree.tostring(tags, encoding='utf8', method='xml').decode('utf-8')
    await writetag(path, xmlstr)
