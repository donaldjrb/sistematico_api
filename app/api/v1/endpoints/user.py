from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


# ---------- ENDPOINTS ----------
@router.get("/", response_model=List[UserOut])
def read_all(db: Session = Depends(get_db)):
    return UserService(db).get_all()


@router.get("/{user_id}", response_model=UserOut)
def read_one(user_id: int, db: Session = Depends(get_db)):
    user = UserService(db).get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.post("/", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(obj_in: UserCreate, db: Session = Depends(get_db)):
    # e-mail único
    if (
        db.query(UserService(db).get_all()[0].__class__)
        .filter_by(email=obj_in.email)
        .first()
    ):
        raise HTTPException(status_code=400, detail="Email already registered")
    return UserService(db).create(obj_in)


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, obj_in: UserUpdate, db: Session = Depends(get_db)):
    updated = UserService(db).update(user_id, obj_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return updated


@router.delete("/{user_id}", response_model=dict)
def deactivate_user(user_id: int, db: Session = Depends(get_db)):
    deleted = UserService(db).delete(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return {"detail": "User deactivated"}
