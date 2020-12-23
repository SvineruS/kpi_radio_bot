import abc
from dataclasses import dataclass
from typing import Optional

from consts.config import AIOHTTP_SESSION
from music._id3 import id3


class Searcher(abc.ABC):
    SESSION = AIOHTTP_SESSION

    URL_MATCHING = ()
    SUPPORT_INLINE = True

    @classmethod
    def is_for_me(cls, query, inline):
        if inline and not cls.SUPPORT_INLINE:
            return False
        for u in cls.URL_MATCHING:
            if u in query:
                return True
        return False

    @classmethod
    @abc.abstractmethod
    async def search(cls, query):
        pass


@dataclass
class AudioResult:
    id: str = None
    url: str = None
    performer: str = None
    title: str = None
    duration: Optional[int] = None

    is_url_downloadable: bool = True
    paste_id3_tags: bool = False

    async def download(self):
        if self.is_url_downloadable:
            return self.url

        bytes_ = b""
        if self.paste_id3_tags:
            # скорее всего часто не будет работать из-за наличия других приоритетных тегов
            # todo проверить
            bytes_ += id3({
                'TPE1': self.performer,
                'TIT2': self.title,
            }).encode('utf-8')
        async with AIOHTTP_SESSION.get(self.url) as resp:
            bytes_ += await resp.read()
        return bytes_
