import abc
from collections import namedtuple

from consts.config import AIOHTTP_SESSION


class Searcher(abc.ABC):
    SESSION = AIOHTTP_SESSION

    @classmethod
    @abc.abstractmethod
    def is_for_me(cls, query):
        pass

    @classmethod
    @abc.abstractmethod
    async def search(cls, query):
        pass


AudioResult = namedtuple('AudioResult', ['url', 'id', 'artist', 'title', 'duration'], defaults=[None])
