import asyncio
from unittest import TestCase

from consts.config import AIOHTTP_SESSION
from music import search


class TestBroadcast(TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def test_search_knowingly_finded(self):
        res = self.loop.run_until_complete(search("test"))
        self.assertTrue(len(res) > 0)

    def test_search_knowingly_not_finded(self):
        res = self.loop.run_until_complete(search("asodjkaliksjdlakjsdl;'kajsd;lkj"))
        self.assertTrue(len(res) == 0)

    async def async_test_download_url(self):
        res = await search("test")
        url = res[0].download_url
        async with AIOHTTP_SESSION.get(url) as res:
            self.assertEqual(200, res.status)
            self.assertEqual('audio/mpeg', res.headers['Content-Type'])

    def test_download_url(self):
        self.loop.run_until_complete(self.async_test_download_url())
