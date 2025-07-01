from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# --- Esquemas para MediaFile ---

class MediaFileBase(BaseModel):
    """
    Esquema base con los campos comunes para un archivo multimedia.
    """
    name: Optional[str] = None
    file_type: Optional[str] = None
    url: Optional[str] = None
    status: bool = True
    duration_seconds: int = 10

class MediaFileCreate(MediaFileBase):
    """
    Esquema para la creación de un nuevo archivo multimedia en la base de datos.
    Hereda todos los campos de MediaFileBase.
    """
    name: str
    file_type: str
    url: str
    company_id: int

class MediaFileUpdate(BaseModel):
    """
    Esquema para actualizar un archivo multimedia existente.
    Todos los campos son opcionales.
    """
    name: Optional[str] = None
    status: Optional[bool] = None
    duration_seconds: Optional[int] = None

class MediaFileInDBBase(MediaFileBase):
    """
    Esquema base para los datos de un archivo tal como están en la DB.
    """
    id: int
    company_id: int
    date_create: datetime

    class Config:
        from_attributes = True

class MediaFile(MediaFileInDBBase):
    """
    Esquema principal para devolver en la API.
    Este es el modelo que se enviará a los clientes.
    """
    pass

