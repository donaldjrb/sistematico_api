from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, get_settings
from app.schemas.token import RefreshTokenRequest, Token
from app.schemas.user import UserCreate
from app.services.user_service import UserService

router = APIRouter()
settings = get_settings()
refresh_store = {}  # key = user_id, value = refresh token


@router.post("/register", response_model=dict, tags=["auth"])
def register(data: UserCreate, db: Session = Depends(get_db)):
    svc = UserService(db)
    user = svc.create(
        full_name=data.full_name,
        email=data.email,
        password=data.password,
        role=data.role,
        company_id=1,
    )
    return {"id": user.id, "email": user.email}


@router.post("/login", response_model=Token, tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    svc = UserService(db)
    user = svc.authenticate(email=form.username, password=form.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials"
        )

    access_token = create_access_token({"sub": user.id})
    refresh_token = create_access_token(
        {"sub": user.id}, expires_minutes=43200
    )  # 30 días

    refresh_store[user.id] = refresh_token

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token, tags=["auth"])
def refresh_token_endpoint(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    token = payload.token
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        user_id: int | None = payload.get("sub")
        if user_id is None or refresh_store.get(user_id) != token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access = create_access_token({"sub": user_id})
    new_refresh = create_access_token({"sub": user_id}, expires_minutes=43200)
    refresh_store[user_id] = new_refresh

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.get("/me", tags=["auth"])
def me(current=Depends(get_current_user)):
    return {"id": current.id, "email": current.email, "role": current.role}
