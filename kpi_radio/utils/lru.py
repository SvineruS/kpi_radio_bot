import asyncio
import functools
from collections import OrderedDict
from time import time


def lru(maxsize: int = None, ttl: int = None):
    def decorator(function):
        cache = LRU(maxsize=maxsize, ttl=ttl)

        def get_key(args, kwargs):
            return tuple(args), tuple(kwargs.items())

        def cache_clear():
            cache.clear()

        def cache_del(*args, **kwargs):
            k = get_key(args, kwargs)
            if k in cache:
                del cache[k]

        if asyncio.iscoroutinefunction(function):
            @functools.wraps(function)
            async def on_call(*args, **kwargs):
                k = get_key(args, kwargs)
                if k in on_call.cache:
                    return on_call.cache[k]
                result = await function(*args, **kwargs)
                on_call.cache[k] = result
                return result
        else:
            @functools.wraps(function)
            def on_call(*args, **kwargs):
                k = get_key(args, kwargs)
                if k in on_call.cache:
                    return on_call.cache[k]
                result = function(*args, **kwargs)
                on_call.cache[k] = result
                return result

        on_call.cache = cache
        on_call.cache_clear = cache_clear
        on_call.cache_del = cache_del

        return on_call

    return decorator


class LRU(OrderedDict):
    def __init__(self, *args, maxsize=None, ttl=None, **kwargs):
        self.maxsize = maxsize
        self.ttl = ttl
        super().__init__(*args, **kwargs)

    def __getitem__(self, key):
        val = super().__getitem__(key)
        ttl, value = val
        if ttl and ttl != self._get_ttl():
            del self[key]
            return None
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        val = (self._get_ttl(), value)
        super().__setitem__(key, val)
        if self.maxsize and len(self) > self.maxsize:
            del self[next(iter(self))]

    def _get_ttl(self):
        if not self.ttl:
            return None
        return round(time() / self.ttl)


__all__ = ['lru', 'LRU']
