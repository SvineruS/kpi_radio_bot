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


async def search_text(name, attempt2=False):
    url = "https://genius.com/api/search/multi?q=" + quote_plus(name)
    resp = await asession.get(url)

    if resp.status_code != 200:
        return False

    s = loads(resp.text)
    s = s['response']['sections']
    for t in s:
        if t['type'] == 'song':
            s = t
            break

    if not s['hits']:
        if attempt2:
            return False
        name = name.split('- ')[-1]
        return await search_text(name, True)

    s = s['hits'][0]['result']
    title = s['full_title']

    resp2 = await asession.get(s['url'])

    if resp2.status_code != 200:
        return False

    lyrics = resp2.html.find("div.lyrics", first=True).text

    return title, lyrics


async def is_anime(audio_name):
    text = (await asession.get(f"https://www.google.com.ua/search?q={quote_plus(audio_name)}")).text.lower()
    return any(anime_word in text for anime_word in consts.anime_words)
