# app/schemas/token.py
from pydantic import BaseModel
from typing import Optional

# Se importa el schema de salida que SÍ CONTIENE el service_id
from .user import UserOut

class Token(BaseModel):
    access_token: str
    token_type: str
    # Se especifica que el objeto 'user' debe seguir la estructura de UserOut
    user: UserOut

class TokenData(BaseModel):
    # 'sub' (subject) se usa para almacenar el ID del usuario dentro del JWT
    sub: Optional[str] = None

