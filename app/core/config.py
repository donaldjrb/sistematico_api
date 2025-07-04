# Ruta: app/core/config.py
from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Base de datos ─────────────────────────────────────────────
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_pass: str

    # ── JWT ───────────────────────────────────────────────────────
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ── CORS ──────────────────────────────────────────────────────
    # URL del frontend autorizado; por defecto el típico Vite/React local
    frontend_url: AnyHttpUrl = "http://localhost:5173"

    # --- INICIO DE MODIFICACIÓN ---
    # ── URL Pública de la Aplicación ──────────────────────────────
    # Esta es la URL base que será accesible desde otros dispositivos en la red.
    # Debe configurarse en el archivo .env.
    # Ejemplo: APP_PUBLIC_URL=http://10.1.2.15:8080
    APP_PUBLIC_URL: str = Field(default="http://localhost:8080", alias="APP_PUBLIC_URL")
    # --- FIN DE MODIFICACIÓN ---

    # ── Configuración de pydantic-settings ────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # ── Propiedades derivadas ─────────────────────────────────────
    @property
    def database_url(self) -> str:
        """Cadena de conexión completa para SQLAlchemy."""
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # ── Rate-limit ───────────────
    requests_per_minute: int = 60

@lru_cache
def get_settings() -> Settings:
    """Devuelve una instancia cacheada para inyección en FastAPI."""
    return Settings()
