import abc
from dataclasses import dataclass
from typing import Optional, Tuple

from consts.config import AIOHTTP_SESSION
from music.search._tagger import ffmpeg_metadata


class Searcher(abc.ABC):
    SESSION = AIOHTTP_SESSION

    URL_MATCHING: Tuple[str, ...] = ()
    SUPPORT_INLINE = True

    @classmethod
    def is_for_me(cls, query: str, inline: bool):
        if inline and not cls.SUPPORT_INLINE:
            return False
        for u in cls.URL_MATCHING:
            if u in query:
                return True
        return False

    @classmethod
    @abc.abstractmethod
    async def search(cls, query: str):
        pass


@dataclass
class AudioResult:
    id: str
    url: str
    performer: str
    title: str
    duration: Optional[int] = None

    is_url_downloadable: bool = True
    paste_metadata: bool = False

    async def download(self):
        if self.is_url_downloadable:
            return self.url

        async with AIOHTTP_SESSION.get(self.url) as resp:
            bytes_ = await resp.read()

        if self.paste_metadata:
            bytes_ = await ffmpeg_metadata(bytes_, duration=self.duration, title=self.title, author=self.performer)

        return bytes_
