import asyncio
from unittest import TestCase

from consts.config import AIOHTTP_SESSION
from music import search, check


class TestMusicSearch(TestCase):
    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def test_search_knowingly_finded(self):
        res = self.loop.run_until_complete(search("test"))
        self.assertTrue(len(res) > 0)

    def test_search_knowingly_not_finded(self):
        res = self.loop.run_until_complete(search("asodjkaliksjdlakjsdl;'kajsd;lkj"))
        self.assertTrue(len(res) == 0)

    def test_youtube_search(self):
        res = self.loop.run_until_complete(
            search("https://music.youtube.com/watch?v=BaMcFghlVEU&list=RDAMVMBaMcFghlVEU"))
        self.assertTrue(len(res) == 1)
        self.assertEqual(res[0].title, "♂GACHILLMUCHI♂")

    async def async_test_download_url(self):
        res = await search("test")
        url = res[0].url
        async with AIOHTTP_SESSION.get(url) as res:
            self.assertEqual(200, res.status)
            self.assertEqual('audio/mpeg', res.headers['Content-Type'])

    def test_download_url(self):
        self.loop.run_until_complete(self.async_test_download_url())

    def test_check(self):
        self.loop.run_until_complete(self._test_check())

    async def _test_check(self):
        self.assertTrue(await check.is_anime("Batta - chase"))
        self.assertFalse(await check.is_anime("Плюнь мне в жопу"))

        self.assertFalse(await check.is_contain_bad_words("Batta - chase"))
        self.assertTrue(await check.is_contain_bad_words("Плюнь мне в жопу"))
