__all__ = ("router",)

from aiogram import Router

from .client import router as client_router
from .admin import router as admin_router
from .employee import router as employee_router

router = Router(name=__name__)

router.include_routers(
    admin_router,
    employee_router,
    client_router
)

# this one has to be the last!
# router.include_router(common_router)