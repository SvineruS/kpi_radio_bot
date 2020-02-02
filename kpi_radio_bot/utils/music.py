import logging
from json import loads
from urllib.parse import quote_plus

from requests_html import AsyncHTMLSession

import consts

asession = AsyncHTMLSession()


async def search(name):
    url = "http://svinua.cf/api/music/?search=" + quote_plus(name)
    resp = await asession.get(url)
    if resp.status_code != 200:
        return False
    try:
        return loads(resp.text)
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
    res = await asession.get(url)
    if res.status_code != 200:
        return False

    res_json = loads(res.text)
    sections = res_json['response']['sections']
    for sec in sections:
        if sec['type'] == 'song' and sec['hits']:
            break
    else:  # если не брейк
        return False

    res = sec['hits'][0]['result']

    title = res['full_title']
    lyrics_url = res['url']

    res = await asession.get(lyrics_url)
    if res.status_code != 200:
        return False

    lyrics = res.html.find("div.lyrics", first=True).text

    return title, lyrics


async def is_anime(audio_name):
    text = (await asession.get(f"https://www.google.com.ua/search?q={quote_plus(audio_name)}")).text.lower()
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
