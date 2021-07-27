import asyncio
from unittest import TestCase

from utils.lru import lru


class MyLruDecoratorTest(TestCase):

    def setUp(self):
        @lru()
        async def my_function(*args, **kwargs):
            self.func_completed += 1

        self.func_completed = 0
        self.func = my_function

    def run_func(self, *args, **kwargs):
        asyncio.run(self.func(*args, **kwargs))

    def test_attrs(self):
        self.assertTrue(hasattr(self.func, 'cache'))
        self.assertTrue(hasattr(self.func, 'cache_clear'))
        self.assertTrue(hasattr(self.func, 'cache_del'))

    def test_test(self):
        self.run_func('foo', foo='bar')
        self.assertEqual(self.func_completed, 1)

    def test_cache(self):
        self.run_func('foo', foo='bar')
        self.run_func('foo', foo='bar')
        self.assertEqual(self.func_completed, 1)

    def test_clear(self):
        self.run_func('foo', foo='bar')
        self.func.cache_clear()
        self.run_func('foo', foo='bar')
        self.assertEqual(self.func_completed, 2)

    def test_del(self):
        self.run_func('foo', foo='bar')
        self.func.cache_del('foo', foo='bar')
        self.run_func('foo', foo='bar')
        self.assertEqual(self.func_completed, 2)

    def test_noargs(self):
        self.run_func()
        self.run_func()
        self.assertEqual(self.func_completed, 1)

    def test_noargs_clear(self):
        self.run_func()
        self.func.cache_clear()
        self.run_func()
        self.assertEqual(self.func_completed, 2)

    def test_noargs_del(self):
        self.run_func()
        self.func.cache_del()
        self.run_func()
        self.assertEqual(self.func_completed, 2)
