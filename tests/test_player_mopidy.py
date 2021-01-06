import asyncio
from unittest import TestCase

from player.player import PlayerMopidy


class TestPlayerMopidy(TestCase):

    def test_set_volume(self):
        asyncio.run(self._test_set_volume())

    async def _test_set_volume(self):
        client = await PlayerMopidy.get_client()
        for i in (5, 55):
            await PlayerMopidy.set_volume(i)
            self.assertEqual(i, await client.mixer.get_volume())

    def test_set_next_track(self):
        self.fail()

    def test_add_track(self):
        self.fail()

    def test_remove_track(self):
        self.fail()

    def test_get_playlist(self):
        self.fail()

    def test_get_prev_now_next(self):
        self.fail()
