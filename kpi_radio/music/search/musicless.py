from typing import List
from urllib.parse import quote_plus

from music.search.searcher import Searcher, AudioResult
from utils.lru import lru

_BASE_URL = "http://api.svinua.tk/musicless/"


class Musicless(Searcher):

    @classmethod
    def is_for_me(cls, query: str, inline: bool):
        return True  # musicless is fallback

    @classmethod
    @lru(maxsize=200, ttl=60 * 60 * 12)
    async def search(cls, query: str) -> List[AudioResult]:
        url = _BASE_URL + "search/" + quote_plus(query)
        async with cls.SESSION.get(url) as res:
            res.raise_for_status()
            return [
                _to_object(i)
                for i in await res.json(content_type=None)
            ]


def _to_object(audio: dict) -> AudioResult:
    id_ = f"{audio['owner_id']}_{audio['id']}"
    return AudioResult(
        url=_BASE_URL + "download_by_id/" + quote_plus(id_) + "?lol",
        id=id_,
        performer=audio['artist'],
        title=audio['title'],
        duration=audio['duration'],
    )
