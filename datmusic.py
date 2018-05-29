import requests
from json import loads as json_decode


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
        url = 'https://api-2.datmusic.xyz/dl/' + url
    try:
        s = requests.get(url, headers={'referer': "https://datmusic.xyz/"}, stream=True)
        if s.status_code != 200:
            print('Error: datmusic-download not 200')
            return False
        return s.raw
    except Exception as e:
        print('Error: download song!', e)
        return False
