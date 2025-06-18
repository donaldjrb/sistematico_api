# app/api/v1/api.py
from fastapi import APIRouter

from app.api.v1.endpoints import (
    advertisement,
    auth,
    close_reason,
    company,
    media_file,
    service,
    ticket,
    user,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth")
api_router.include_router(company.router)
api_router.include_router(service.router)
api_router.include_router(ticket.router)
api_router.include_router(user.router)
api_router.include_router(close_reason.router)
api_router.include_router(advertisement.router)
api_router.include_router(media_file.router)
