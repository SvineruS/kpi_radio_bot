from ._base import PlayerBase
from player.player_utils import radioboss


class PlayerRadioboss(PlayerBase):
    @classmethod
    async def set_volume(cls, volume, fade=500):
        return await radioboss.setvol(volume, fade)

    @classmethod
    async def next_track(cls):
        return await radioboss.cmd_next()

    @classmethod
    async def set_next_track(cls, pos):
        return await radioboss.setnexttrack(pos)

    @classmethod
    async def add_track(cls, path, position):
        position = -2 if position == 0 else position
        return await radioboss.inserttrack(path, position)

    @classmethod
    async def remove_track(cls, position):
        return await radioboss.delete(position)

    @classmethod
    async def get_playlist(cls):
        return (await radioboss.getplaylist2())['TRACK']

    @classmethod
    async def get_prev_now_next(cls):
        playback = await radioboss.playbackinfo()
        if not playback or playback['Playback']['@state'] == 'stop':
            return None

        result = [''] * 3
        for i, k in enumerate(('PrevTrack', 'CurrentTrack', 'NextTrack')):
            title = playback[k]['TRACK']['@CASTTITLE']
            if "setvol" not in title:
                result[i] = title
        return result
