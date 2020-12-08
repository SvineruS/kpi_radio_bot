from player import radioboss


class PlayerBase:
    @classmethod
    async def set_volume(cls, volume):
        raise NotImplementedError

    @classmethod
    async def next_track(cls):
        raise NotImplementedError


class PlayerRadioboss(PlayerBase):
    @classmethod
    async def set_volume(cls, volume, fade=500):
        await radioboss.setvol(volume, fade)

    @classmethod
    async def next_track(cls):
        await radioboss.cmd_next()

    @classmethod
    async def set_next_track(cls, pos):
        await radioboss.setnexttrack(pos)


Player = PlayerRadioboss
