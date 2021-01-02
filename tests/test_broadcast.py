from unittest import TestCase

from player import Broadcast
from utils import DateTime


class DateTimeFake(DateTime):
    _time = None

    @classmethod
    def set_time(cls, time):
        cls._time = time
        return cls

    @classmethod
    def fromtimestamp(cls, t, tz=None):
        a = super(cls, DateTimeFake).fromtimestamp(cls._time)
        return a

    @classmethod
    def now(cls):
        return cls.fromtimestamp(None)


class TestBroadcast(TestCase):

    def test_creation(self):
        Broadcast(1, 1)
        with self.assertRaises(Exception):
            Broadcast(-1, 1)
        with self.assertRaises(Exception):
            Broadcast(1, -1)

    def test_singleton(self):
        b11 = Broadcast(1, 1)
        b22 = Broadcast(2, 2)
        b11_ = Broadcast(1, 1)
        b22_ = Broadcast(2, 2)

        self.assertIs(b11, b11_)
        self.assertIs(b22, b22_)
        self.assertIsNot(b11, b22)

    def test_now(self):
        dt = DateTimeFake.set_time(DateTime(2021, 1, 1, 8, 5, 0).timestamp())
        Broadcast.datetime = dt
        br = Broadcast.now()
        self.assertTrue(br.is_now())
        self.assertTrue(br.is_today())
        self.assertIs(br, Broadcast(4, 0))
        self.assertIs(br, Broadcast.get_closest())

    def test_relative_time(self):
        dt = DateTimeFake.set_time(DateTime(2021, 1, 1, 8, 5, 0).timestamp())
        Broadcast.datetime = dt
        br = Broadcast(4, 1)
        self.assertFalse(br.is_already_play_today())
        self.assertTrue(br.is_will_be_play_today())





