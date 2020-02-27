import os
from datetime import datetime
from functools import lru_cache

from aiogram import types

from config import BOT, ADMINS_CHAT_ID, PATH_SELF


def get_audio_name(audio: types.Audio) -> str:
    return get_audio_name_(audio.performer, audio.title)


def get_audio_name_(performer, title) -> str:
    if performer and title:
        name = f'{performer} - {title}'
    elif not performer and not title:
        name = 'Названия нету :('
    else:
        name = title if title else performer
    name = ''.join(list(filter(lambda c: (c not in '/:*?"<>|'), name)))  # винда агрится на эти символы в пути
    return name


def get_user_name(user_obj: types.User) -> str:
    return get_user_name_(user_obj.id, user_obj.first_name)


def get_user_name_(id_, name):
    return '<a href="tg://user?id={0}">{1}</a>'.format(id_, name)


def get_user_from_entity(message):
    entities = message.caption_entities if message.audio or message.photo else message.entities
    if entities:
        return entities[0].user


def case_by_num(num: int, c_1: str, c_2: str, c_3: str) -> str:
    if 11 <= num <= 14:
        return c_3
    if num % 10 == 1:
        return c_1
    if 2 <= num % 10 <= 4:
        return c_2
    return c_3


def reboot() -> None:
    os.system(rf'cmd.exe /C start {PATH_SELF}\\update.bat')


async def get_moders():
    @lru_cache(maxsize=1)
    async def get_moders_(_):
        admins = await BOT.get_chat_administrators(ADMINS_CHAT_ID)
        return {
            admin.user.id: admin
            for admin in admins
            # if admin.custom_title
        }

    return await get_moders_(datetime.today().day)


async def get_moder_by_username(username):
    for moder in (await get_moders()).values():
        if moder.user.username == username:
            return moder.user


async def is_moder(user_id):
    member = await BOT.get_chat_member(ADMINS_CHAT_ID, user_id)
    return member and member.status in ('creator', 'administrator', 'member')
