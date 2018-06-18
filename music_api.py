import requests
from json import loads as json_decode
from bs4 import BeautifulSoup


def search(name):
    url = "https://api-2.datmusic.xyz/search?q={0}&page=0".format(name)
    try:
        s = requests.get(url, headers={'referer': "https://datmusic.xyz/"})
        if s.status_code != 200:
            print('Error: datmusic-search not 200')
            return False
        s = json_decode(s.text)
        if s['status'] != 'ok' or not s['data']:
            return False
        return s['data']
    except Exception as e:
        print('Error: find song!', e)
        return False


def download(url, short=False):
    if short:
        url = 'https://api-2.datmusic.xyz/dl/' + url.replace('.mp3', '')
    try:
        s = requests.get(url, headers={'referer': "https://datmusic.xyz/"}, stream=True)
        if s.status_code != 200:
            print('Error: datmusic-download not 200')
            return False
        return s.raw
    except Exception as e:
        print('Error: download song!', e)
        return False


def search_text(name, attempt2=False):
    s = requests.get("https://genius.com/api/search/multi?q=" + name)
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
        name = name.split('- ')[1]
        return search_text(name, True)

    s = s['hits'][0]['result']['url']

    s = requests.get(s)
    if s.status_code != 200:
        return 'Ошибка взятия текста'

    t = BeautifulSoup(s.text, "html.parser")
    t = t.find("div", class_="lyrics")
    t = t.get_text()
    return t
