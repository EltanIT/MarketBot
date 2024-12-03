from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode


TOKEN='7733547498:AAGfS-lZK4qrHhVn22o267_nmFgp4xvbEmM'


bot = Bot(
            token = TOKEN, 
            default = DefaultBotProperties(
                                            parse_mode=ParseMode.HTML
                                        )
        )
bot.admins_list = []
bot.employees_list = []

dp = Dispatcher()
