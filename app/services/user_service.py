from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- CRUD ----------
    def get_all(self) -> List[User]:
        return self.db.query(User).all()

    def get(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, obj_in: UserCreate) -> User:
        db_user = User(
            full_name=obj_in.full_name,
            email=obj_in.email,
            hashed_password=hash_password(obj_in.password),
            role=obj_in.role,
            is_active=obj_in.is_active,
            company_id=obj_in.company_id,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update(self, user_id: int, obj_in: UserUpdate) -> Optional[User]:
        user = self.get(user_id)
        if not user:
            return None
        for field, value in obj_in.dict(exclude_unset=True).items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get(user_id)
        if not user:
            return False
        user.is_active = False  # soft-delete
        self.db.commit()
        return True

    # ---------- auth helper ----------
    def authenticate(self, *, email: str, password: str) -> Optional[User]:
        user = self.db.query(User).filter_by(email=email, is_active=True).first()
        if user and verify_password(password, user.hashed_password):
            return user
        return None
