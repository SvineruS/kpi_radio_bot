class PlayerBase:
    @classmethod
    async def set_volume(cls, volume):
        raise NotImplementedError

    @classmethod
    async def next_track(cls):
        raise NotImplementedError

    @classmethod
    async def set_next_track(cls, pos):
        raise NotImplementedError

    @classmethod
    async def add_track(cls, path, position):
        raise NotImplementedError

    @classmethod
    async def remove_track(cls, position):
        raise NotImplementedError

    @classmethod
    async def get_playlist(cls):
        raise NotImplementedError

    @classmethod
    def get_prev_now_next(cls):
        raise NotImplementedError
