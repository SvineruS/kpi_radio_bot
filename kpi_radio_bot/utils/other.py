import functools
from collections import OrderedDict
from html.parser import HTMLParser
from time import time


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
