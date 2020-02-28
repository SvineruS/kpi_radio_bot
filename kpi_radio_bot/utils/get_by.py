"""Методы, конвентирующие всякую хрень"""
from datetime import datetime

from aiogram import types


def get_audio_name(audio: types.Audio) -> str:
    return get_audio_name_(audio.performer, audio.title)


def get_audio_name_(performer, title) -> str:
    if performer and title:
        name = f'{performer} - {title}'
    elif not performer and not title:
        name = 'Названия нету'
    else:
        name = title if title else performer
    name = ''.join(list(filter(lambda c: (c not in '/:*?"<>|'), name)))  # винда агрится на эти символы в пути
    return name


def get_user_name(user_obj: types.User) -> str:
    return get_user_name_(user_obj.id, user_obj.first_name)


def get_user_name_(id_: int, name: str) -> str:
    return '<a href="tg://user?id={0}">{1}</a>'.format(id_, name)


def get_user_from_entity(message):
    entities = message.caption_entities if message.audio or message.photo else message.entities
    if not entities:
        return False
    return entities[0].user


def case_by_num(num: int, c_1: str, c_2: str, c_3: str) -> str:
    if 11 <= num <= 14:
        return c_3
    if num % 10 == 1:
        return c_1
    if 2 <= num % 10 <= 4:
        return c_2
    return c_3


def time_to_datetime(time):
    return datetime.combine(datetime.today(), time)
