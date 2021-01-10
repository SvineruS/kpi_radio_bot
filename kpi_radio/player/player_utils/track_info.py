# todo ffmpeg or something instead of radioboss

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from player.backends.radioboss._radioboss_api import _write_comment_tag, _read_comment_tag


@dataclass
class TrackInfo:
    id: int
    name: str
    moderation_id: int

    @classmethod
    async def read(cls, path: Path) -> Optional[TrackInfo]:
        if not (tag := await _read_comment_tag(path)):
            return None

        try:
            return TrackInfo(**json.loads(tag))
        except json.JSONDecodeError:
            return None

    @classmethod
    async def clear(cls, path: Path) -> bool:
        return await _write_comment_tag(path, '')

    async def write(self, path: Path):
        tag = json.dumps(self.__dict__)
        return await _write_comment_tag(path, tag)


__all__ = ['TrackInfo']
