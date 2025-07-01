from typing import Optional
from pydantic import BaseModel

# Esquema base con los campos que pueden ser compartidos.
# La descripción es opcional aquí para máxima flexibilidad.
class AdvertisementBase(BaseModel):
    description: Optional[str] = None
    is_active: bool = True
    company_id: int


# Esquema para la creación. Hereda de la base y asegura que
# la descripción sea obligatoria al crear un nuevo anuncio.
class AdvertisementCreate(AdvertisementBase):
    description: str


# --- INICIO DE LA CORRECCIÓN QUIRÚRGICA ---
# Esquema para la actualización. Los campos deben ser opcionales
# para permitir actualizaciones parciales (solo cambiar la descripción o solo el estado).
class AdvertisementUpdate(BaseModel):
    description: Optional[str] = None
    is_active: Optional[bool] = None
# --- FIN DE LA CORRECCIÓN QUIRÚRGICA ---


# Esquema para la salida de datos de la API.
# Muestra todos los campos relevantes de un anuncio.
class AdvertisementOut(BaseModel):
    id: int
    description: Optional[str] = None
    is_active: bool
    company_id: int

    # Configuración para Pydantic v2 para que funcione con modelos SQLAlchemy
    class Config:
        from_attributes = True
