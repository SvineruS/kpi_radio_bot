"""Добавляет в message_handler параметры
https://aiogram.readthedocs.io/en/latest/dispatcher/filters.html#boundfilter

Текущие параметры:
 - admins_chat,     срабатывает только если сообщение с админского чата
 - pm,              срабатывает только если сообщение написано боту в личку
 - reply_to_bot,    срабатывает только если сообщение это реплай на сообщение бота
 # - only_admin,    срабатывает только если сообщение написал участник админского чата
"""

from aiogram.dispatcher.filters.filters import BoundFilter
from aiogram.types import Message, ChatType

from config import ADMINS_CHAT_ID, BOT


class AdminChatFilter(BoundFilter):
    key = 'admins_chat'

    def __init__(self, admins_chat):
        self.admins_chat = admins_chat

    async def check(self, message: Message):
        if not self.admins_chat:
            return True
        return message.chat.id == ADMINS_CHAT_ID


class PrivateChatFilter(BoundFilter):
    key = 'pm'

    def __init__(self, pm):
        self.pm = pm

    async def check(self, message: Message):
        if not self.pm:
            return True
        return ChatType.is_private(message)


class ReplyToBotFilter(BoundFilter):
    key = 'reply_to_bot'

    def __init__(self, reply_to_bot):
        self.reply_to_bot = reply_to_bot

    async def check(self, message: Message):
        if not self.reply_to_bot:
            return True
        return message.reply_to_message and message.reply_to_message.from_user.id == (await BOT.me).id


# class OnlyAdminFilter(BoundFilter):
#     key = 'only_admin'
#
#     def __init__(self, only_admin):
#         self.only_admin = only_admin
#
#     async def check(self, message):
#         if not self.only_admin:
#             return True
#         if message.chat.id == ADMINS_CHAT_ID:
#             return True
#         return is_admin(message.from_user.id)


def bind_filters(dp_):
    dp_.filters_factory.bind(AdminChatFilter)
    dp_.filters_factory.bind(ReplyToBotFilter)
    dp_.filters_factory.bind(PrivateChatFilter)
