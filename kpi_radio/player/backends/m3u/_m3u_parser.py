"""Че то мне пиздец не нравятся готовые реализации"""
from collections import namedtuple
from pathlib import Path
from typing import List, Iterable

Track = namedtuple("Track", ('performer', 'title', 'path', 'duration'))


def load(path: Path) -> Iterable[Track]:
    try:
        with path.open() as f:
            if not f.readline().startswith('#EXTM3U'):
                return

            for track in f:
                if not track.startswith('#EXTINF:'):
                    continue
                duration, _performer_title = track.strip()[8:].split(', ')
                performer, title = _performer_title.split(' - ')
                audio_path = next(f).strip()
                yield Track(performer, title, audio_path, int(duration))
    except FileNotFoundError:
        return


def dump(path: Path, playlist: List[Track]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as f:
        f.write('#EXTM3U\n')

        for track in playlist:
            f.write(f"#EXTINF:{track.duration}, {track.performer} - {track.title}\n{track.path}\n")
