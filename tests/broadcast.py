from unittest import TestCase

from kpi_radio_bot.broadcast import playlist, Broadcast
import datetime

dt = datetime.datetime(2019, 11, 11, 8, 20, 0)


class MyDate(datetime.date):
    @classmethod
    def now(cls):
        return dt


class TestBroadcast(TestCase):
    def test_now_is_now(self):
        playlist.datetime = MyDate

        b = Broadcast.now()
        self.assertIsNotNone(b)

    def test_singletone(self):
        b11 = Broadcast(1, 1)
        b22 = Broadcast(2, 2)
        b11_ = Broadcast(1, 1)
        b22_ = Broadcast(2, 2)

        self.assertIs(b11, b11_)
        self.assertIs(b22, b22_)
        self.assertIsNot(b11, b22)
