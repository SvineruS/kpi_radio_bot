import logging
import xml.etree.ElementTree as Etree  # для апи радиобосса
from urllib.parse import quote_plus

import aiohttp
from bs4 import BeautifulSoup

from config import *


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


async def radioboss_api(**kwargs):
    url = 'http://{}:{}/?pass={}'.format(*RADIOBOSS_DATA)
    for key in kwargs:
        url += '&{0}={1}'.format(key, quote_plus(str(kwargs[key])))
    t = 'Еще даже не подключился к радиобоссу а уже эксепшены(('
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.encoding = 'utf-8'
                t = await resp.text()
                if not t:
                    return False
                if t == 'OK':
                    return True
                return Etree.fromstring(t)
    except Exception as e:
        logging.error(f'radioboss: {e} {t} {url}')
        return False
