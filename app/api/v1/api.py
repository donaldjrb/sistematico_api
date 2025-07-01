from fastapi import APIRouter

from app.api.v1.endpoints import (
    advertisement,
    auth,
    close_reason,
    company,
    service,
    ticket,
    user,
    cashier,
    display
)

router = APIRouter()

router.include_router(advertisement.router, prefix="/advertisement", tags=["Advertisement"])
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(close_reason.router, prefix="/close_reason", tags=["Close Reason"])
router.include_router(company.router, prefix="/company", tags=["Company"])
router.include_router(service.router, prefix="/service", tags=["Service"])
router.include_router(ticket.router, prefix="/ticket", tags=["Ticket"])
router.include_router(user.router, prefix="/user", tags=["User"])
router.include_router(cashier.router, prefix="/cashier", tags=["Cashier"])
router.include_router(display.router, prefix="/ws/display", tags=["WebSocket Display"])
