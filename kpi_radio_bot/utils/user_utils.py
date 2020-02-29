from typing import Dict

from aiogram.types import ChatMember, User

from config import BOT, ADMINS_CHAT_ID
from utils.other import my_lru


@my_lru(maxsize=1, ttl=60 * 60 * 12)
async def get_admins() -> Dict[int, ChatMember]:
    admins = await BOT.get_chat_administrators(ADMINS_CHAT_ID)
    return {
        admin.user.id: admin
        for admin in admins
    }


@my_lru(maxsize=10, ttl=60 * 60 * 12)
async def get_admin_by_username(username: str) -> User:
    for admin in (await get_admins()).values():
        if admin.user.username == username:
            return admin.user


@my_lru(maxsize=10, ttl=60 * 60 * 12)
async def is_admin(user_id: int) -> bool:
    member = await BOT.get_chat_member(ADMINS_CHAT_ID, user_id)
    return member and member.status in ('creator', 'administrator', 'member')
