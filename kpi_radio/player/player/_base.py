from pathlib import Path


class PlayerBase:
    @classmethod
    async def set_volume(cls, volume: int):
        raise NotImplementedError

    @classmethod
    async def next_track(cls):
        raise NotImplementedError

    @classmethod
    async def set_next_track(cls, pos: int):
        raise NotImplementedError

    @classmethod
    async def add_track(cls, path: Path, position: int):
        raise NotImplementedError

    @classmethod
    async def remove_track(cls, position: int):
        raise NotImplementedError

    @classmethod
    async def get_playlist(cls):
        raise NotImplementedError

    @classmethod
    async def get_prev_now_next(cls):
        raise NotImplementedError

    @classmethod
    async def play_playlist(cls, path: Path):
        raise NotImplementedError
