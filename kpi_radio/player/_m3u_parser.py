"""Че то мне пиздец не нравятся готовые реализации"""
from collections import namedtuple
from typing import List, Iterable

Track = namedtuple("Track", ('title', 'path', 'duration'))


def load(filepath) -> Iterable[Track]:
    try:
        with open(filepath) as f:
            if not f.readline().startswith('#EXTM3U'):
                return

            for track in f:
                if not track.startswith('#EXTINF:'):
                    continue
                # duration, artist_title = track.removeprefix('#EXTINF:').split(', ')
                duration, artist_title = track.strip()[8:].split(', ')
                # artist, title = artist_title.split(' - ')
                path = next(f).strip()
                yield Track(artist_title, path, int(duration))
    except FileNotFoundError:
        return


def dump(filepath, playlist: List[Track]):
    with open(filepath, 'w') as f:
        f.write('#EXTM3U\n')

        for track in playlist:
            f.write(f"#EXTINF:{track.duration}, {track.title}\n{track.path}\n")
