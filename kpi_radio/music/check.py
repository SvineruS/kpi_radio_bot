from typing import Optional, Tuple, List
from urllib.parse import quote_plus

from consts import others, config
from utils.lru import lru
from .text import search_text


@lru(maxsize=100, ttl=60 * 60 * 12)
async def is_anime(audio_name: str) -> bool:
    async with config.AIOHTTP_SESSION.get(f"https://www.google.com.ua/search?q={quote_plus(audio_name)}",
                                          headers={'user-agent': 'my custom agent'}) as res:
        if res.status != 200:
            return False
        text = (await res.text()).lower()

    return any(anime_word in text for anime_word in others.ANIME_WORDS)


def is_bad_name(audio_name: str) -> bool:
    audio_name = audio_name.lower()
    return any(bad_name in audio_name for bad_name in others.BAD_NAMES)


async def is_contain_bad_words(audio_name: str) -> bool:
    return (res := await get_bad_words(audio_name)) is not None and res[1]


@lru(maxsize=100, ttl=60 * 60 * 12)
async def get_bad_words(audio_name: str) -> Optional[Tuple[str, List[str]]]:
    if not (res := await search_text(audio_name)):
        return None

    title, lyrics = res
    b_w = [word for word in others.BAD_WORDS if word in lyrics]
    return title, b_w
