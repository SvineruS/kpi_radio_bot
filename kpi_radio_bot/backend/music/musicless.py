import logging
from collections import namedtuple
from json import JSONDecodeError
from typing import List
from urllib.parse import urlencode

from aiohttp import ClientResponseError

from consts.config import AIOHTTP_SESSION
from utils.lru import lru

Audio = namedtuple('Audio', ('artist', 'id', 'title', 'duration', 'download_url'))
_BASE_URL = "http://api.svinua.cf/musicless/?"


@lru(maxsize=200, ttl=60 * 60 * 12)
async def search(name: str) -> List[Audio]:
    url = _BASE_URL + urlencode(dict(search=name))

    async with AIOHTTP_SESSION.get(url) as res:
        try:
            res.raise_for_status()
            audio = await res.json(content_type=None)
            audio = [_to_object(i) for i in audio]
            return audio
        except (JSONDecodeError, ClientResponseError) as ex:
            logging.error(f'search song: {ex} {name}')
            return []


#


def _to_object(audio: dict) -> Audio:
    return Audio(
        id=f"{audio['owner_id']}_{audio['id']}",
        artist=audio['artist'],
        title=audio['title'],
        duration=audio['duration'],
        download_url=_get_download_url(audio)
    )


def _get_download_url(audio: dict) -> str:
    return _BASE_URL + urlencode(dict(download=audio['url'], artist=audio['artist'], title=audio['title']))
