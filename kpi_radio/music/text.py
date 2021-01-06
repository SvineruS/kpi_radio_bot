import logging
import re
from html.parser import HTMLParser
from json import JSONDecodeError
from typing import Optional, Tuple
from urllib.parse import quote_plus

from aiohttp import ClientResponseError

from consts.config import AIOHTTP_SESSION
from utils.lru import lru


class MyHTMLParser(HTMLParser):
    data = ''

    def parse(self, data):
        self.data = ''
        self.feed(data)
        return self.data

    def handle_starttag(self, tag, attrs):
        if tag == 'br':
            self.data += '\n'

    def handle_data(self, data):
        self.data += data

    def error(self, message):
        # ignore
        pass


_RE_GENIUS_BRACKETS = re.compile(r" \([\w\d ]+\)")
_PARSER = MyHTMLParser()


@lru(maxsize=100, ttl=60 * 60 * 12)
async def search_text(name: str) -> Optional[Tuple[str, str]]:
    if not (res_json := await _search(name)):
        return None
    if not (song := _get_song_section(res_json['response']['sections'])):
        return None
    if not (lyrics := await _get_lyrics(song['url'])):
        return None
    title = _delete_translit_from_title(song['full_title'])
    return title, lyrics


#


async def _search(name: str) -> Optional[dict]:
    url = "https://genius.com/api/search/multi?q=" + quote_plus(name)
    async with AIOHTTP_SESSION.get(url) as res:
        try:
            res.raise_for_status()
            return await res.json(content_type=None)
        except (JSONDecodeError, ClientResponseError) as ex:
            logging.warning(f"search song text: {ex} {name}")
            return None


def _get_song_section(sections: dict) -> Optional[dict]:
    for sec in sections:
        if sec['type'] == 'song' and sec['hits']:
            return sec['hits'][0]['result']
    return None


def _delete_translit_from_title(title: str) -> str:
    return _RE_GENIUS_BRACKETS.sub("", title)


async def _get_lyrics(url: str) -> Optional[str]:
    async with AIOHTTP_SESSION.get(url) as res:
        if res.status != 200:
            return None
        lyrics = await res.text()

    try:
        if '<div class="lyrics">' in lyrics:
            lyrics = lyrics.split('<div class="lyrics">')[1].split('</div>')[0]
        elif '<div class="Lyrics__Container' in lyrics:
            lyrics = lyrics.split('<div class="Lyrics__Container')[1].split('">', 1)[1].split('</div>')[0]
        else:
            logging.warning(f"lyrics search error. url: {url}, хз короче")
        lyrics = _PARSER.parse(lyrics).strip()
        return lyrics
    except Exception as ex:
        logging.warning(f"lyrics search error. url: {url}, exception: {ex}")
        return None
