from datetime import datetime


class DateTime(datetime):
    @classmethod
    def day_num(cls) -> int:
        return cls.today().weekday()

    @classmethod
    def from_time(cls, time):
        return cls.combine(cls.today(), time)
