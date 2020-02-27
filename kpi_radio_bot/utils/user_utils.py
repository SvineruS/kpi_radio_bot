from config import BOT, ADMINS_CHAT_ID
from utils.other import my_lru


def get_user_from_entity(message):
    entities = message.caption_entities if message.audio or message.photo else message.entities
    if not entities:
        return False
    return entities[0].user


@my_lru(maxsize=1, ttl=60 * 60 * 12)
async def get_admins():
    admins = await BOT.get_chat_administrators(ADMINS_CHAT_ID)
    return {
        admin.user.id: admin
        for admin in admins
    }


@my_lru(maxsize=10, ttl=60 * 60 * 12)
async def get_admin_by_username(username):
    for admin in (await get_admins()).values():
        if admin.user.username == username:
            return admin.user


@my_lru(maxsize=10, ttl=60 * 60 * 12)
async def is_admin(user_id):
    member = await BOT.get_chat_member(ADMINS_CHAT_ID, user_id)
    return member and member.status in ('creator', 'administrator', 'member')
