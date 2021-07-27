"""Методы, конвентирующие всякую хрень"""
from aiogram.types import Message, User, Audio


def get_audio_name(audio: Audio) -> str:
    return get_audio_name_(audio.performer, audio.title)


def get_audio_name_(performer: str, title: str) -> str:
    if performer and title:
        name = f'{performer} - {title}'
    elif not performer and not title:
        name = 'Названия нету'
    else:
        name = title if title else performer
    name = ''.join(list(filter(lambda c: (c not in '/:*?"<>|'), name)))  # винда агрится на эти символы в пути
    return name


def get_user_name(user_obj: User) -> str:
    return get_user_name_(user_obj.id, user_obj.first_name)


def get_user_name_(id_: int, name: str) -> str:
    return f'<a href="tg://user?id={id_}">{name}</a>'


def get_user_from_entity(message: Message) -> User:
    entities = message.caption_entities if message.audio or message.photo else message.entities
    if not entities:
        raise ValueError
    return entities[0].user


def case_by_num(num: int, c_1: str, c_2: str, c_3: str) -> str:
    if 11 <= num <= 14:
        return c_3
    if num % 10 == 1:
        return c_1
    if 2 <= num % 10 <= 4:
        return c_2
    return c_3
