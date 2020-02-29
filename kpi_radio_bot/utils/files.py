"""Методы для работы с файлами"""

import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

from aiogram.types import Audio

import consts
from broadcast.broadcast import get_broadcast_path


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
        day = datetime.now().weekday()
    src = str(get_broadcast_path(day))  # заказы
    dst = str(consts.PATHS['archive'])  # архив

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


async def download_audio(audio: Audio, path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    await audio.download(path, timeout=60)


def get_downloaded_tracks(day: int, time: int) -> List[Path]:
    path = get_broadcast_path(day, time)
    try:
        return [file for file in path.iterdir() if file.is_file()]
    except FileNotFoundError as ex:
        logging.warning(f'get_downloaded_tracks: {ex}')
        return []
