import logging
from pathlib import Path
from typing import Union, Optional, Iterable
from urllib.parse import quote_plus

import aiohttp
import xmltodict

from consts.config import RADIOBOSS_DATA, AIOHTTP_SESSION


async def setvol(vol: int, fade: int = 500) -> bool:
    return bool(await _radioboss_api(cmd=f'setvol {vol} {fade}'))


async def cmd_next() -> bool:
    return bool(await _radioboss_api(cmd='next'))


async def move(pos1: int, pos2: int) -> bool:
    return bool(await _radioboss_api(action='move', pos1=pos1, pos2=pos2))


async def inserttrack(filename: Path, pos: int) -> bool:
    return bool(await _radioboss_api(action='inserttrack', filename=filename, pos=pos))


async def setnexttrack(pos: int) -> bool:
    return bool(await _radioboss_api(action='setnexttrack', pos=pos))


async def delete(pos: Union[int, str, Iterable[int]]) -> bool:
    if isinstance(pos, list):
        pos = ','.join(map(str, pos))
    return bool(await _radioboss_api(action='delete', pos=pos))


async def playbackinfo() -> dict:
    playback = await _radioboss_api(action='playbackinfo')
    assert isinstance(playback, dict)
    return playback['Info']


async def getplaylist2(cnt: int = 100) -> dict:
    playlist = await _radioboss_api(action='getplaylist2', cnt=cnt)
    assert isinstance(playlist, dict)
    return playlist['Playlist']


async def getlastplayed() -> dict:
    lastplayed = await _radioboss_api(action='getlastplayed')
    assert isinstance(lastplayed, dict)
    return lastplayed['LastPlayed']


async def readtag(filename: Path) -> Optional[dict]:
    if not (tag := await _radioboss_api(action='readtag', fn=filename)):
        return None
    assert isinstance(tag, dict)
    return tag


async def writetag(filename: Path, data: str) -> bool:
    return bool(await _radioboss_api(action='writetag', fn=filename, data=data))


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

    except (aiohttp.ClientConnectionError, Exception) as ex:
        logging.error(f'radioboss: {ex} {res} {url}')
        raise
    

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
