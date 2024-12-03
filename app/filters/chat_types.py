from aiogram.filters import BaseFilter
from aiogram import Bot
from aiogram.types import Message


class IsAdmin(BaseFilter):
    def __init__(self) -> None:
        pass
    

    async def __call__(self, message: Message, bot: Bot) -> bool:
        return message.from_user.id in bot.admins_list
    


class IsEmployee(BaseFilter):
    def __init__(self) -> None:
        pass
    

    async def __call__(self, message: Message, bot: Bot) -> bool:
        return message.from_user.id in bot.employees_list