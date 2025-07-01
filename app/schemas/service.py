# app/schemas/service.py
from pydantic import BaseModel
from typing import Optional

# Esquema base con los campos que el usuario provee al crear o actualizar.
class ServiceBase(BaseModel):
    name: str
    code: Optional[str] = None
    location: Optional[str] = None
    max_capacity: int = 0
    priority_level: int = 0
    requires_payment: bool = False

# Esquema para la creación de un servicio.
# Hereda de ServiceBase, asegurando que todos sus campos son provistos.
class ServiceCreate(ServiceBase):
    pass # El company_id se añadirá en la lógica del backend.

# --- INICIO DE CORRECCIÓN QUIRÚRGICA ---
# Esquema para la actualización. Todos los campos son opcionales
# para permitir actualizaciones parciales (ej. cambiar solo el nombre o solo el estado).
class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    location: Optional[str] = None
    max_capacity: Optional[int] = None
    priority_level: Optional[int] = None
    requires_payment: Optional[bool] = None
    is_active: Optional[bool] = None # Se incluye is_active para poder cambiarlo
# --- FIN DE CORRECCIÓN QUIRÚRGICA ---

# Esquema para la salida de datos (lo que la API devuelve al cliente).
# Incluye todos los campos relevantes del modelo de la base de datos.
class ServiceOut(ServiceBase):
    id: int
    is_active: bool
    company_id: int

    class Config:
        from_attributes = True # Para Pydantic v2