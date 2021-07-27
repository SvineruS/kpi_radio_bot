"""Добавляет в message_handler параметры
https://aiogram.readthedocs.io/en/latest/dispatcher/filters.html#boundfilter

Текущие параметры:
 - admins_chat,         срабатывает только если сообщение с админского чата
 - reply_to_bot_text,   срабатывает, если ответ боту и, если данный текст != True, текст == данному тексту
 - cb,                  срабатывает когда callback_data сделана тем же классом что и данный,
                        добавляет аргумент cb с объектом класса, содержащим аттрибуты спаршенные с коллбека
 # - only_admin,        срабатывает только если сообщение написал участник админского чата
"""

from aiogram.dispatcher.filters.filters import BoundFilter
from aiogram.types import Message, CallbackQuery

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
        if self.text is True:
            return True
        return message.reply_to_message.text == self.text


class JsonCallbackDataFilter(BoundFilter):
    key = 'cb'

    def __init__(self, cb):
        self.cb = cb

    async def check(self, query: CallbackQuery):
        if data := self.cb.from_str(query.data):
            return {'cb': data}


def bind_filters(dp_):
    dp_.filters_factory.bind(AdminChatFilter)
    dp_.filters_factory.bind(ReplyToBotTextFilter)
    dp_.filters_factory.bind(JsonCallbackDataFilter)
