from __future__ import annotations

import logging
from datetime import datetime
from time import time as _time


class DateTime(datetime):
    _fake_time = None

    @classmethod
    def day_num(cls) -> int:
        return cls.today().weekday()

    @classmethod
    def from_time(cls, time):
        return cls.combine(cls.today(), time)

    @classmethod
    def now(cls, tz=None):
        return cls.fromtimestamp(_time(), tz)

    @classmethod
    def fake(cls, dt: DateTime):
        logging.info("faked time to " + str(dt))
        cls._fake_time = dt.timestamp()

    @classmethod
    def fromtimestamp(cls, t, tz=None):
        if cls._fake_time is not None:
            t = cls._fake_time
        return datetime.fromtimestamp(t)

