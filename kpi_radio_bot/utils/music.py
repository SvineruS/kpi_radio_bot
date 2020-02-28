"""Методы, для работы с треками (поиск, поиск текста, определение опенингов и матов)"""

import logging
from urllib.parse import quote_plus

import consts
from config import AIOHTTP_SESSION
from utils.other import MyHTMLParser, my_lru

PARSER = MyHTMLParser()


@my_lru(maxsize=200, ttl=60 * 60 * 12)
async def search(name):
    url = "http://svinua.cf/api/music/?search=" + quote_plus(name)
    async with AIOHTTP_SESSION.get(url) as res:
        if res.status != 200:
            return False
        try:
            return await res.json()
        except Exception as ex:
            logging.error(f'search song: {ex} {name}')
            logging.warning(f"pls add exception {ex} in except")
            return False


def get_download_url(url, artist=None, title=None):
    url = f'http://svinua.cf/api/music/?download={url}'
    if artist:
        url += '&artist=' + quote_plus(artist)
    if title:
        url += '&title=' + quote_plus(title)
    return url


@my_lru(maxsize=100, ttl=60 * 60 * 12)
async def search_text(name):
    url = "https://genius.com/api/search/multi?q=" + quote_plus(name)
    async with AIOHTTP_SESSION.get(url) as res:
        if res.status != 200:
            return False

        res_json = await res.json(content_type=None)

    sections = res_json['response']['sections']
    for sec in sections:
        if sec['type'] == 'song' and sec['hits']:
            break
    else:  # если не брейк
        return False

    res = sec['hits'][0]['result']

    title = res['full_title']
    lyrics_url = res['url']

    async with AIOHTTP_SESSION.get(lyrics_url) as res:
        if res.status != 200:
            return False
        lyrics = await res.text()
    lyrics = lyrics.split('<div class="lyrics">')[1].split('</div>')[0]
    lyrics = PARSER.parse(lyrics).strip()
    return title, lyrics


@my_lru(maxsize=100, ttl=60 * 60 * 12)
async def is_anime(audio_name):
    async with AIOHTTP_SESSION.get(f"https://www.google.com.ua/search?q={quote_plus(audio_name)}",
                                   headers={'user-agent': 'my custom agent'}) as res:
        if res.status != 200:
            return False
        text = (await res.text()).lower()

    # todo проверять реджексом с учетом конца слова
    return any(anime_word in text for anime_word in consts.ANIME_WORDS)


def is_bad_name(audio_name):
    audio_name = audio_name.lower()
    return any(bad_name in audio_name for bad_name in consts.BAD_NAMES)


async def is_contain_bad_words(audio_name):
    res = await get_bad_words(audio_name)
    return res and res[1]


@my_lru(maxsize=100, ttl=60 * 60 * 12)
async def get_bad_words(audio_name):
    res = await search_text(audio_name)
    if not res:
        return False

    title, lyrics = res
    b_w = [word for word in consts.BAD_WORDS if word in lyrics]
    return title, b_w
