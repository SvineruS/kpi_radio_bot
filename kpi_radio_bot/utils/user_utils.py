from functools import lru_cache

from config import BOT, ADMINS_CHAT_ID


def get_user_from_entity(message):
    entities = message.caption_entities if message.audio or message.photo else message.entities
    if not entities:
        return False
    return entities[0].user


@lru_cache(maxsize=1)
async def get_admins():
    admins = await BOT.get_chat_administrators(ADMINS_CHAT_ID)
    return {
        admin.user.id: admin
        for admin in admins
    }


@lru_cache(maxsize=10)
async def get_admin_by_username(username):
    for admin in (await get_admins()).values():
        if admin.user.username == username:
            return admin.user


@lru_cache(maxsize=10)
async def is_admin(user_id):
    member = await BOT.get_chat_member(ADMINS_CHAT_ID, user_id)
    return member and member.status in ('creator', 'administrator', 'member')
