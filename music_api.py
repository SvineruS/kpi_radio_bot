import aiohttp
import logging
from bs4 import BeautifulSoup
from urllib.parse import quote
from config import *
import urllib.parse
import xml.etree.ElementTree as Etree  # для апи радиобосса


async def search(name):
    url = "http://svinua.cf/api/music/?search={}".format(quote(name))
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                assert resp.status == 200
                return await resp.json()
    except Exception as e:
        logging.error(f'search song: {e} {name}')
        return False


def get_download_url(url, artist=None, title=None, bitrate=64):
    return f'http://svinua.cf/api/music/?download={url}'
    # old download
    url = f'http://svinua.cf/api/music/?download={url}&bitrate={bitrate}'
    if artist:
        url += '&artist=' + urllib.parse.quote_plus(artist)
    if title:
        url += '&title=' + urllib.parse.quote_plus(title)
    return url


#  deprecated
async def download(url):
    url = f'http://svinua.cf/api/music/?download={url}'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                assert resp.status == 200
                return await resp.read()
    except Exception as e:
        logging.error(f'download song: {e} {url}')
        return False


async def search_text(name, attempt2=False):
    url = "https://genius.com/api/search/multi?q=" + quote(name)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            assert resp.status == 200

            s = await resp.json()
            s = s['response']['sections']
            for t in s:
                if t['type'] == 'song':
                    s = t
                    break

            if not s['hits']:
                if attempt2:
                    return 'Ошибка поиска'
                name = name.split('- ')[-1]
                return await search_text(name, True)

            s = s['hits'][0]['result']
            title = s['full_title']

            async with session.get(s['url']) as resp2:
                assert resp.status == 200

                t = await resp2.text()
                t = BeautifulSoup(t, "html.parser")
                t = t.find("div", class_="lyrics")
                t = t.get_text()

                return title + '\n\n' + t


async def radioboss_api(**kwargs):
    url = 'http://{}:{}/?pass={}'.format(*RADIOBOSS_DATA)
    for key in kwargs:
        url += '&{0}={1}'.format(key, quote(str(kwargs[key])))
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
