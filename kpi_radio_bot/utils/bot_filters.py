"""Добавляет в message_handler параметры, например admins_chat
https://aiogram.readthedocs.io/en/latest/dispatcher/filters.html#boundfilter"""

from aiogram.dispatcher.filters.filters import BoundFilter

from config import ADMINS_CHAT_ID


class AdminChatFilter(BoundFilter):
    key = 'admins_chat'

    def __init__(self, admins_chat):
        self.admins_chat = admins_chat

    async def check(self, message):
        if not self.admins_chat:
            return True
        return message.chat.id == ADMINS_CHAT_ID


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
