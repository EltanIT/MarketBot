__all__ = ("router",)

from aiogram import Router

from app.filters.chat_types import IsAdmin

from .AdminHandler import router as admin_handler

router = Router(name=__name__)

router.message.filter(IsAdmin())
router.callback_query.filter(IsAdmin())

router.include_routers(
    admin_handler
)