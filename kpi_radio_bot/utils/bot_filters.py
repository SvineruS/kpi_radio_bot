from aiogram.dispatcher.filters.filters import BoundFilter
from config import ADMINS_CHAT_ID


class OnlyAdminsFilter(BoundFilter):
    key = 'only_admins'

    def __init__(self, only_admins):
        self.only_admins = only_admins

    async def check(self, message):
        if not self.only_admins:
            return True
        return message.chat.id == ADMINS_CHAT_ID


def bind_filters(dp):
    dp.filters_factory.bind(OnlyAdminsFilter)
