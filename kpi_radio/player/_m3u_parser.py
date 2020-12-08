"""Че то мне пиздец не нравятся готовые реализации"""
from collections import namedtuple
from typing import List, AsyncGenerator

import aiofiles


Track = namedtuple("Track", ('title', 'path', 'duration'))


async def load(filepath) -> AsyncGenerator[Track, None]:
    try:
        async with aiofiles.open(filepath) as f:
            if not (await f.readline()).startswith('#EXTM3U'):
                return

            async for track in f:
                if not track.startswith('#EXTINF:'):
                    continue
                # duration, artist_title = track.removeprefix('#EXTINF:').split(', ')
                duration, artist_title = track.strip()[8:].split(', ')
                # artist, title = artist_title.split(' - ')
                path = (await f.__anext__()).strip()
                yield Track(artist_title, path, int(duration))
    except FileNotFoundError:
        return


async def dump(filepath, playlist: List[Track]):
    async with aiofiles.open(filepath, 'w') as f:
        await f.write('#EXTM3U\n')

        for track in playlist:
            await f.write(f"#EXTINF:{track.duration}, {track.title}\n{track.path}\n")
