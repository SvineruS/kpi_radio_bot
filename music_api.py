import requests
import logging
from json import loads as json_decode
from bs4 import BeautifulSoup
from urllib.parse import quote
from config import *
import xml.etree.ElementTree as Etree  # для апи радиобосса


def search(name):
    url = "http://svinua.cf/api/music/?search={}".format(quote(name))
    try:
        s = requests.get(url)
        if s.status_code != 200:
            logging.error(f'svinua audio api wtf')
            return False

        return json_decode(s.text)
    except Exception as e:
        logging.error(f'search song: {e} {name}')
        return False


def download(url):
    try:
        s = requests.get('http://svinua.cf/api/music/?download=' + url, stream=True)
        if s.status_code != 200:
            logging.error(f'svinua audio api wtf')
            return False
        return s.raw
    except Exception as e:
        logging.error(f'download song: {e} {url}')
        return False


def search_text(name, attempt2=False):
    s = requests.get("https://genius.com/api/search/multi?q=" + quote(name))
    if s.status_code != 200:
        return 'Ошибка доступа'
    s = json_decode(s.text)
    s = s['response']['sections']
    for t in s:
        if t['type'] == 'song':
            s = t
            break

    if not s['hits']:
        if attempt2:
            return 'Ошибка поиска'
        name = name.split('- ')[-1]
        return search_text(name, True)

    s = s['hits'][0]['result']
    title = s['full_title']

    r = requests.get(s['url'])
    if r.status_code != 200:
        return 'Ошибка взятия текста'

    t = BeautifulSoup(r.text, "html.parser")
    t = t.find("div", class_="lyrics")
    t = t.get_text()

    return title + '\n\n' + t


def radioboss_api(**kwargs):
    url = 'http://{}:{}/?pass={}'.format(*RADIOBOSS_DATA)
    for key in kwargs:
        url += '&{0}={1}'.format(key, quote(str(kwargs[key])))
    t = 'Еще даже не подключился к радиобоссу а уже эксепшены(('
    try:
        t = requests.get(url)
        t.encoding = 'utf-8'
        t = t.text
        if not t:
            return False
        if t == 'OK':
            return True
        return Etree.fromstring(t)
    except Exception as e:
        logging.error(f'radioboss: {e} {t} {url}')
        return False
