import logging
from html.parser import HTMLParser
from urllib.parse import quote_plus

import consts
from config import AIOHTTP_SESSION


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


PARSER = MyHTMLParser()


async def search(name):
    url = "http://svinua.cf/api/music/?search=" + quote_plus(name)
    async with AIOHTTP_SESSION.get(url) as res:
        if res.status != 200:
            return False
        try:
            return await res.json()
        except Exception as e:
            logging.error(f'search song: {e} {name}')
            return False


def get_download_url(url, artist=None, title=None):
    url = f'http://svinua.cf/api/music/?download={url}'
    if artist:
        url += '&artist=' + quote_plus(artist)
    if title:
        url += '&title=' + quote_plus(title)
    return url


async def search_text(name):
    url = "https://genius.com/api/search/multi?q=" + quote_plus(name)
    async with AIOHTTP_SESSION.get(url) as res:
        if res.status != 200:
            return False
        res_json = await res.json()

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


async def is_anime(audio_name):
    async with AIOHTTP_SESSION.get(f"https://www.google.com.ua/search?q={quote_plus(audio_name)}") as res:
        if res.status != 200:
            return False
        text = await res.text().lower()
    return any(anime_word in text for anime_word in consts.ANIME_WORDS)


def is_bad_performer(performer):
    performer = performer.lower()
    return any(bad_perf in performer for bad_perf in consts.BAD_PERFORMERS)


async def is_contain_bad_words(audio_name):
    res = await search_text(audio_name)
    return res and res[1]


async def get_bad_words(audio_name):
    res = await search_text(audio_name)
    if not res:
        return False

    title, lyrics = res
    bw = [word for word in consts.BAD_WORDS if word in lyrics]
    return title, bw
