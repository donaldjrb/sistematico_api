# app/schemas/user.py
from typing import Optional
from pydantic import BaseModel

# Esquema base con los campos comunes
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    role: str

# Esquema para la creación de un usuario.
# Hereda de la base y añade los campos específicos para la creación.
class UserCreate(UserBase):
    password: str
    # --- INICIO DE MODIFICACIÓN ---
    # service_id es opcional, ya que no todos los roles lo necesitan.
    service_id: Optional[int] = None
    # --- FIN DE MODIFICACIÓN ---

# Esquema para la actualización. Todos los campos son opcionales.
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None
    # --- INICIO DE MODIFICACIÓN ---
    service_id: Optional[int] = None
    # --- FIN DE MODIFICACIÓN ---


# Esquema para la salida de datos (lo que la API devuelve).
class UserOut(UserBase):
    id: int
    company_id: int
    # --- INICIO DE MODIFICACIÓN ---
    service_id: Optional[int] = None # Devolvemos el service_id para que el frontend lo conozca
    # --- FIN DE MODIFICACIÓN ---

    class Config:
        from_attributes = True # Para Pydantic v2
