from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.close_reason import CloseReason  # tu modelo real
from app.schemas.close_reason import CloseReasonCreate, CloseReasonUpdate


class CloseReasonService:
    def __init__(self, db: Session):
        self.db = db

    # ---------- CRUD ----------
    def get_all(self) -> List[CloseReason]:
        return self.db.query(CloseReason).all()

    def get(self, reason_id: int) -> Optional[CloseReason]:
        return self.db.query(CloseReason).filter(CloseReason.id == reason_id).first()

    def create(self, obj_in: CloseReasonCreate) -> CloseReason:
        db_reason = CloseReason(**obj_in.dict())
        self.db.add(db_reason)
        self.db.commit()
        self.db.refresh(db_reason)
        return db_reason

    def update(
        self, reason_id: int, obj_in: CloseReasonUpdate
    ) -> Optional[CloseReason]:
        reason = self.get(reason_id)
        if not reason:
            return None
        for field, value in obj_in.dict(exclude_unset=True).items():
            setattr(reason, field, value)
        self.db.commit()
        self.db.refresh(reason)
        return reason

    def delete(self, reason_id: int) -> bool:
        reason = self.get(reason_id)
        if not reason:
            return False
        reason.is_active = False  # soft-delete
        self.db.commit()
        return True
