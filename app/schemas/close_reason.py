from typing import Optional
from pydantic import BaseModel

# Esquema base con los campos que el usuario provee.
class CloseReasonBase(BaseModel):
    reason_text: str


# Esquema para la creación (lo que se recibe en el endpoint POST).
# Hereda de la base. El `company_id` se añadirá en la lógica del backend.
class CloseReasonCreate(CloseReasonBase):
    pass


# Esquema para la actualización (lo que se recibe en el endpoint PUT/PATCH).
# Todos los campos son opcionales para permitir actualizaciones parciales.
class CloseReasonUpdate(BaseModel):
    reason_text: Optional[str] = None
    is_active: Optional[bool] = None


# Esquema para la salida de datos de la API (lo que se devuelve en los GET).
# Incluye todos los campos relevantes del modelo de la base de datos.
class CloseReasonOut(CloseReasonBase):
    id: int
    is_active: bool
    company_id: int

    class Config:
        from_attributes = True # para Pydantic v2
