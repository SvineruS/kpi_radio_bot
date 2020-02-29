import json
import logging
import xml.etree.ElementTree as Etree
from pathlib import Path
from typing import Union
from urllib.parse import quote_plus

from aiogram.types import User

from config import RADIOBOSS_DATA, AIOHTTP_SESSION


async def radioboss_api(**kwargs) -> Union[Etree.Element, bool]:
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
    except Exception as ex:
        logging.error(f'radioboss: {ex} {res} {url}')
        logging.warning(f"pls pls add exception {type(ex)}{ex}in except")
        return False


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
    tags = await radioboss_api(action='readtag', fn=path)
    tag = tags[0].attrib['Comment']
    try:
        return json.loads(tag)
    except json.JSONDecodeError:
        logging.warning(f"can't read track comment")


async def clear_track_additional_info(path: Path):
    await _write_comment_tag(path, '')


#


async def _write_comment_tag(path: Path, tag: str):
    tags = await radioboss_api(action='readtag', fn=path)
    tags[0].attrib['Comment'] = tag
    xmlstr = Etree.tostring(tags, encoding='utf8', method='xml').decode('utf-8')
    await radioboss_api(action='writetag', fn=path, data=xmlstr)
