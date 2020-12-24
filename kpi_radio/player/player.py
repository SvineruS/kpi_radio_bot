from player.player_utils import radioboss


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

    @classmethod
    async def add_track(cls, path, position):
        position = -2 if position == 0 else position
        await radioboss.inserttrack(path, position)

    @classmethod
    async def remove_track(cls, position):
        await radioboss.delete(position)

    @classmethod
    async def get_playlist(cls):
        return (await radioboss.getplaylist2())['TRACK']

    @classmethod
    def get_prev_now_next(cls):
        playback = await radioboss.playbackinfo()
        if not playback or playback['Playback']['@state'] == 'stop':
            return None

        result = [''] * 3
        for i, k in enumerate(('PrevTrack', 'CurrentTrack', 'NextTrack')):
            title = playback[k]['TRACK']['@CASTTITLE']
            if "setvol" not in title:
                result[i] = title
        return result


Player = PlayerRadioboss
