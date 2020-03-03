import json
import logging
from pathlib import Path
from typing import Union, Optional
from urllib.parse import quote_plus

import aiohttp
import xmltodict
from aiogram.types import User

from consts.config import RADIOBOSS_DATA, AIOHTTP_SESSION


async def setvol(vol: int, fade: int = 500) -> bool:
    return await _radioboss_api(cmd=f'setvol {vol} {fade}')


async def cmd_next() -> bool:
    return await _radioboss_api(cmd='next')


async def move(pos1: int, pos2: int) -> bool:
    return await _radioboss_api(action='move', pos1=pos1, pos2=pos2)


async def inserttrack(filename: Path, pos: int) -> bool:
    return await _radioboss_api(action='inserttrack', filename=filename, pos=pos)


async def setnexttrack(pos: int) -> bool:
    return await _radioboss_api(action='setnexttrack', pos=pos)


async def delete(pos: int) -> bool:
    return await _radioboss_api(action='delete', pos=pos)


async def playbackinfo() -> Optional[dict]:
    if not (playback := await _radioboss_api(action='playbackinfo')):
        return None
    return playback['Info']


async def getplaylist2(cnt: int = 100) -> Optional[dict]:
    if not (playlist := await _radioboss_api(action='getplaylist2', cnt=cnt)):
        return None
    return playlist['Playlist']


async def readtag(filename: Path) -> Optional[dict]:
    if not (tag := await _radioboss_api(action='readtag', fn=filename)):
        return None
    return tag


async def writetag(filename: Path, data: str) -> bool:
    return await _radioboss_api(action='writetag', fn=filename, data=data)


#


async def write_track_additional_info(path: Path, user_obj: User, moderation_id: int) -> bool:
    tag = {
        'id': user_obj.id,
        'name': user_obj.first_name,
        'moderation_id': moderation_id
    }
    tag = json.dumps(tag)
    return await _write_comment_tag(path, tag)


async def read_track_additional_info(path: Path) -> Optional[dict]:
    if not (tag := await _read_comment_tag(path)):
        return None

    try:
        return json.loads(tag)
    except json.JSONDecodeError:
        logging.warning(f"can't read track comment")
        return None


async def clear_track_additional_info(path: Path) -> bool:
    return await _write_comment_tag(path, '')


#

async def _radioboss_api(**kwargs) -> Union[dict, bool]:
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
        return xmltodict.parse(res)

    except aiohttp.ClientConnectionError as ex:
        logging.error(f'radioboss: {ex} {res} {url}')
        return False
    except Exception as ex:
        logging.warning(f"pls add exception {type(ex)}{ex}in except")
        return False


async def _write_comment_tag(path: Path, tag: str) -> bool:
    if not (tag_info := await readtag(path)):
        return False
    tag_info['TagInfo']['File']['@Comment'] = tag
    xml_str = xmltodict.unparse(tag_info)
    return await writetag(path, xml_str)


async def _read_comment_tag(path: Path) -> Optional[str]:
    if not (tag_info := await readtag(path)):
        return None
    return tag_info['TagInfo']['File']['@Comment']
