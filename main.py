import asyncio
import logging

from app.config import dp, bot
from db.models import async_main

from app.handlers import router


async def main():
    await async_main()

    dp.include_router(router)
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == '__main__':


    # Раскомментировать, если нужно посмотреть информацию в консоли
    # logging.basicConfig(level=logging.INFO) 

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Exit")
