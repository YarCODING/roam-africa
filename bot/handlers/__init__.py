from aiogram import Router
from .start import router as start_router
from .profile import router as profile_router
from .tours import router as tours_router
from .support import router as support_router
from .booking import router as booking_router

main_router = Router()
main_router.include_routers(
    start_router,
    profile_router,
    tours_router,
    support_router,
    booking_router,
)