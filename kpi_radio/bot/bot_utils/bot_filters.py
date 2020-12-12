"""Добавляет в message_handler параметры
https://aiogram.readthedocs.io/en/latest/dispatcher/filters.html#boundfilter

Текущие параметры:
 - admins_chat,         срабатывает только если сообщение с админского чата
 - reply_to_bot_text,   срабатывает, если ответ боту и, если данный текст != None, текст == данному тексту
 - cb,                  срабатывает только если распаршенная коллбек дата поэлементно совпадает с данным списком,
                        коллбек дата запаршена в модуле keyboards, длинна >= данного списка.
                        Лишние элементы не учитываются в фильтре и возвращаются как аргумент json_data
 # - only_admin,        срабатывает только если сообщение написал участник админского чата
"""

from aiogram.dispatcher.filters.filters import BoundFilter, Filter
from aiogram.types import Message, CallbackQuery

from bot.bot_utils.keyboards import unparse
from consts.config import ADMINS_CHAT_ID, BOT


class AdminChatFilter(BoundFilter):
    key = 'admins_chat'

    def __init__(self, admins_chat):
        self.admins_chat = admins_chat

    async def check(self, message: Message):
        if not self.admins_chat:
            return True
        return message.chat.id == ADMINS_CHAT_ID


class ReplyToBotTextFilter(BoundFilter):
    key = 'reply_to_bot_text'

    def __init__(self, reply_to_bot_text):
        self.text = reply_to_bot_text

    async def check(self, message: Message):
        if not message.reply_to_message or not message.reply_to_message.from_user.id == (await BOT.me).id:
            return False
        if self.text is None:
            return True
        return message.reply_to_message.text == self.text


class JsonCallbackDataFilter(Filter):
    def __init__(self, cb: tuple, mapping: dict):
        self.cb = cb
        self.mapping = mapping

    @classmethod
    def validate(cls, full_config):
        if 'cb' in full_config:
            return {
                'cb': full_config.pop('cb'),
                'mapping': full_config.pop('cb_map', ()),
            }

    async def check(self, query: CallbackQuery):
        data = unparse(query.data)
        if not all((data[i] == cbi for i, cbi in enumerate(self.cb))):
            return
        data = data[len(self.cb):]
        return {
            m: data[i]
            for i, m in enumerate(self.mapping)
        }


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
    dp_.filters_factory.bind(ReplyToBotTextFilter)
    dp_.filters_factory.bind(JsonCallbackDataFilter)
