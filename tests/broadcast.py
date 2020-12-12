from unittest import TestCase

from player import Broadcast


class TestBroadcast(TestCase):
    def test_singletone(self):
        b11 = Broadcast(1, 1)
        b22 = Broadcast(2, 2)
        b11_ = Broadcast(1, 1)
        b22_ = Broadcast(2, 2)

        self.assertIs(b11, b11_)
        self.assertIs(b22, b22_)
        self.assertIsNot(b11, b22)
