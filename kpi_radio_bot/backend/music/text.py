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
        pass


_RE_GENIUS_BRACKETS = re.compile(r" \([\w\d ]+\)")
PARSER = MyHTMLParser()


@lru(maxsize=100, ttl=60 * 60 * 12)
async def search_text(name: str) -> Optional[Tuple[str, str]]:
    url = "https://genius.com/api/search/multi?q=" + quote_plus(name)
    async with AIOHTTP_SESSION.get(url) as res:
        try:
            res.raise_for_status()
            res_json = await res.json(content_type=None)
        except (JSONDecodeError, ClientResponseError) as ex:
            logging.warning(f"search song text: {ex} {name}")
            return None

    sections = res_json['response']['sections']
    for sec in sections:
        if sec['type'] == 'song' and sec['hits']:
            break
    else:  # если не брейк
        return None

    res = sec['hits'][0]['result']

    title = res['full_title']
    lyrics_url = res['url']

    async with AIOHTTP_SESSION.get(lyrics_url) as res:
        if res.status != 200:
            return None
        lyrics = await res.text()

    title = _RE_GENIUS_BRACKETS.sub("", title)  # убрать транслитерацию в скобках

    lyrics = lyrics.split('<div class="lyrics">')[1].split('</div>')[0]
    lyrics = PARSER.parse(lyrics).strip()

    return title, lyrics
