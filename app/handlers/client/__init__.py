__all__ = ("router",)

from aiogram import Router, F

from .ClientHandler import router as client_handler
from .select_product import router as select_product_router
from .client_order import router as client_order_router
from .create_order import router as create_order_router
from .redact_order import router as redact_order_router
from .create_order_from_employee import router as create_order_from_employee_router

router = Router(name=__name__)
router.message.filter(F.chat.type.in_({"private"}))

router.include_routers(
    select_product_router,
    redact_order_router,
    client_order_router,
    create_order_from_employee_router,
    create_order_router,
    client_handler,
)