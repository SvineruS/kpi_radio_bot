from typing import List

from .musicless import Musicless
from .youtube import YouTube
from .searcher import AudioResult

_SEARCHERS = [YouTube, Musicless]  # order is important


async def search(query: str, inline: bool = False) -> List[AudioResult]:
    for s in _SEARCHERS:
        if not s.is_for_me(query, inline):
            continue
        res = await s.search(query)
        if res:
            return res
    return []

__all__ = ['search', 'AudioResult']
