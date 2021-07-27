from typing import Dict, Optional

from aiogram.types import ChatMember, User

from consts.config import ADMINS_CHAT_ID, BOT
from utils.lru import lru


@lru(maxsize=1, ttl=60 * 60 * 12)
async def get_admins() -> Dict[int, ChatMember]:
    admins = await BOT.get_chat_administrators(ADMINS_CHAT_ID)
    return {
        admin.user.id: admin
        for admin in admins
    }


@lru(maxsize=10, ttl=60 * 60 * 12)
async def get_admin_by_username(username: str) -> Optional[User]:
    for admin in (await get_admins()).values():
        if admin.user.username == username:
            return admin.user
    return None


@lru(maxsize=10, ttl=60 * 60 * 12)
async def is_admin(user_id: int) -> bool:
    member = await BOT.get_chat_member(ADMINS_CHAT_ID, user_id)
    return member and member.status in ('creator', 'administrator', 'member')


async def get_moders() -> Dict[int, User]:
    return {
        moder_id: moder.user
        for moder_id, moder in (await get_admins()).items()
        if _is_moder(moder)
    }


#


def _is_moder(moder: ChatMember) -> bool:
    return moder.custom_title and 'Модер' in moder.custom_title
