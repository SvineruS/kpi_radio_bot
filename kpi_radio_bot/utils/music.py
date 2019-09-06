import logging
from urllib.parse import quote_plus

import aiohttp
from bs4 import BeautifulSoup


async def search(name):
    url = "http://svinua.cf/api/music/?search={}".format(quote_plus(name))
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                assert resp.status == 200
                return await resp.json()
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

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                return False

            s = await resp.json()
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

            async with session.get(s['url']) as resp2:
                if resp2.status != 200:
                    return False

                t = await resp2.text()
                t = BeautifulSoup(t, "html.parser")
                t = t.find("div", class_="lyrics")
                t = t.get_text()

                return title + '\n\n' + t
