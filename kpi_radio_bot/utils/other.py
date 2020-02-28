import functools
from collections import OrderedDict
from html.parser import HTMLParser
from time import time


def my_lru(maxsize=None, ttl=None):
    def decorator(function):
        function.cache = LRU(maxsize=maxsize, ttl=ttl)

        @functools.wraps(function)
        async def wrapper(*args, **kwargs):
            result = await function(*args, **kwargs)
            function.cache[tuple(args), tuple(kwargs.items())] = result
            return result

        return wrapper

    return decorator


class LRU(OrderedDict):
    def __init__(self, *args, maxsize=None, ttl=None, **kwargs):
        self.maxsize = maxsize
        self.ttl = ttl
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        t = super().__getitem__(key)
        ttl, value = t
        if ttl and ttl != self.get_ttl():
            del self[key]
            return None
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        t = (self.get_ttl(), value)
        super().__setitem__(key, t)
        if len(self) > self.maxsize:
            del self[next(iter(self))]

    def get_ttl(self):
        if not self.ttl:
            return None
        return round(time() / self.ttl)


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


_hashtag_chars = "0-9,a-z," \
    "\u00c0-\u00d6,\u00d8-\u00f6,\u00f8-\u00ff,\u0100-\u024f," \
    "\u1e00-\u1eff,\u0400-\u0481,\u0500-\u0527,\ua640-\ua66f," \
    "\u0e01-\u0e31,\u1100-\u11ff,\u3130-\u3185,\uA960-\uA97d," \
    "\uAC00-\uD7A0,\uff41-\uff5a,\uff66-\uff9f,\uffa1-\uffbc"

_hashtag_chars = ''.join(
    set(
        chr(ch_id).lower()
        for from_ch, to_ch in
        [
            map(ord, range_.split('-'))
            for range_ in _hashtag_chars.split(',')
        ]
        for ch_id in range(from_ch + 1, to_ch)
    )
)


def id_2_hashtag(id_):
    base = len(_hashtag_chars)
    res = ""
    while id_:
        x, k = divmode(id_, base)
        res += _hashtag_chars[k]
    return res
