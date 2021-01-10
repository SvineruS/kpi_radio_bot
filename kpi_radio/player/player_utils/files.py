"""Методы для работы с файлами"""

import logging
import os
import shutil
from pathlib import Path
from random import choice
from typing import List, Optional

from aiogram.types import Audio

from consts.others import PATHS
from utils import DateTime


def delete_file(path: Path) -> None:
    if not path.exists():
        return
    try:
        path.unlink()
    except Exception as ex:
        logging.warning(f"pls pls add exception {type(ex)}{ex}in except")
        logging.error(f'delete file: {ex} {path}')


def move_to_archive(day: int = None) -> None:
    if not day:
        day = DateTime.day_num()
    src = str(PATHS.ORDERS / f"D0{day + 1}")  # заказы
    dst = str(PATHS.ARCHIVE)  # архив

    if not os.path.exists(dst):
        os.makedirs(dst)

    for src_dir, _, files in os.walk(src):
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst, file_)
            try:
                shutil.move(src_file, dst_file)
            except Exception as ex:
                logging.error(f'move file: {ex} {src_file}')
                logging.warning(f"pls pls add exception {type(ex)}{ex}in except")


def get_random_from_archive() -> Optional[Path]:
    tracks = [p for p in PATHS.ARCHIVE.iterdir()]
    if tracks:
        return choice(tracks)
    else:
        logging.warning("ARCHIVE is empty")
        return None


async def download_audio(audio: Audio, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    await audio.download(path, timeout=60)


def get_downloaded_tracks(path: Path) -> List[Path]:
    try:
        return [file for file in path.iterdir() if file.is_file()]
    except FileNotFoundError as ex:
        logging.warning(f'get_downloaded_tracks: {ex}')
        return []
