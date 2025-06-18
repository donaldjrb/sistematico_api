from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.api import api_router
from app.core.config import get_settings

# ────────────────────────────────────────────────────────────
settings = get_settings()

# Rate-limit: 60 peticiones por minuto (o lo que diga settings)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.requests_per_minute}/minute"],
)

app = FastAPI(title="SISTEMATICO 1.0.0")

# Registrar limiter como middleware y su handler de errores 429
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.middleware("http")(limiter.middleware)

# CORS solo para el frontend permitido
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas v1
app.include_router(api_router, prefix="/api/v1")

