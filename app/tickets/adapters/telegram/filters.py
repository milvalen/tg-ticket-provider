from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject


class AdminFilter(BaseFilter):
    def __init__(self, admin_ids: set[int]) -> None:
        self.admin_ids = admin_ids

    async def __call__(self, event: TelegramObject) -> bool:
        uid = None
        if isinstance(event, Message) and event.from_user:
            uid = event.from_user.id
        elif isinstance(event, CallbackQuery) and event.from_user:
            uid = event.from_user.id
        return uid is not None and uid in self.admin_ids
