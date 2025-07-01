from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.core.security import create_access_token, get_settings
from app.schemas.user import UserCreate
from app.services.user_service import UserService

router = APIRouter()
settings = get_settings()
_refresh_store = {}

# --- INICIO DE CORRECCIÓN QUIRÚRGICA ---
# 1. Se añade 'service_id' al esquema de respuesta del usuario.
class UserLoginResponse(BaseModel):
    id: int
    email: str
    company_id: int
    role: str
    full_name: str | None = None
    service_id: int | None = None # CAMBIO AÑADIDO

class TokenLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserLoginResponse
# --- FIN DE CORRECCIÓN QUIRÚRGICA ---

@router.post("/register", response_model=dict, tags=["auth"])
def register(data: UserCreate, db: Session = Depends(get_db)):
    svc = UserService(db)
    user = svc.create(obj_in=data)
    return {"id": user.id, "email": user.email}


@router.post("/login", response_model=TokenLoginResponse, tags=["auth"])
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    svc = UserService(db)
    user = svc.authenticate(email=form.username, password=form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials"
        )
    if user.company_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User company not found in database"
        )
    
    access_token = create_access_token({"sub": user.id})
    refresh_token = create_access_token({"sub": user.id}, expires_minutes=43200)
    _refresh_store[user.id] = refresh_token

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "company_id": user.company_id,
            "role": user.role,
            "full_name": user.full_name,
            # --- INICIO DE CORRECCIÓN QUIRÚRGICA ---
            # 2. Se añade el 'service_id' del usuario a la respuesta.
            "service_id": user.service_id 
            # --- FIN DE CORRECCIÓN QUIRÚRGICA ---
        },
    }

# El resto del archivo no necesita cambios.
@router.post("/refresh", response_model=TokenLoginResponse, tags=["auth"])
def refresh_token_endpoint(
    payload: dict, db: Session = Depends(get_db)
):
    # Aquí iría la lógica de refresco de token
    pass

@router.get("/me", response_model=dict, tags=["auth"])
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "company_id": current_user.company_id,
        "full_name": current_user.full_name,
        "service_id": current_user.service_id # También es buena práctica añadirlo aquí
    }