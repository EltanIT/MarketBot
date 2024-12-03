__all__ = ("router",)

from aiogram import Router

from app.filters.chat_types import IsEmployee

from .EmployeeHandler import router as employee_handler
from .create_order import router as create_order_router
from .redact_new_order import router as redact_new_order_router
from .redact_old_order import router as redact_old_order_router
from .redact_product import router as redact_product_router

router = Router(name=__name__)

router.message.filter(IsEmployee())
router.callback_query.filter(IsEmployee())

router.include_routers(
    redact_product_router,
    create_order_router,
    redact_new_order_router,
    redact_old_order_router,
    employee_handler
)