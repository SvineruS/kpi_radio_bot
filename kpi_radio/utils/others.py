from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

# todo split


class DateTime(datetime):
    _fake: Optional[datetime] = None

    @classmethod
    def day_num(cls) -> int:
        return cls.today().weekday()

    @classmethod
    def now(cls, tz=None):
        return cls._fake if cls._fake else datetime.now(tz)

    @classmethod
    def today(cls):
        return cls._fake.date() if cls._fake else datetime.today()

    @classmethod
    def strpduration(cls, date_string, format_) -> int:
        d = datetime.strptime(date_string, format_)
        return int((d - DateTime(1900, 1, 1)).total_seconds())

    @classmethod
    def strptoday(cls, date_string, format_) -> datetime:
        d = datetime.strptime(date_string, format_)
        return datetime.combine(cls.today(), d.time())

    @classmethod
    def fake(cls, *args):
        cls._fake = datetime(*args)
        logging.info(f"faked time to {cls._fake}")


class Event:
    def __init__(self, name: str = None):
        self._listeners: list = []
        self.name = name

    def handler(self, function):
        self.register(function)
        return function

    def register(self, *listeners):
        list(map(self._listeners.append, listeners))

    async def notify(self, *args):
        logging.info(f"event {self.name} happened ({args})")
        for listener in self._listeners:
            try:
                await listener(*args)
            except Exception:
                logging.exception(f"notified event: '{self.name}', {listener=} {args=}")

    def __call__(self, *args):
        return self.notify(*args)
