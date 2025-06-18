from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.close_reason import (
    CloseReasonCreate,
    CloseReasonOut,
    CloseReasonUpdate,
)
from app.services.close_reason_service import CloseReasonService

router = APIRouter(prefix="/close-reasons", tags=["close_reasons"])


@router.get("/", response_model=List[CloseReasonOut])
def read_all(db: Session = Depends(get_db)):
    return CloseReasonService(db).get_all()


@router.get("/{reason_id}", response_model=CloseReasonOut)
def read_one(reason_id: int, db: Session = Depends(get_db)):
    reason = CloseReasonService(db).get(reason_id)
    if not reason:
        raise HTTPException(404, "Close reason not found")
    return reason


@router.post("/", response_model=CloseReasonOut, status_code=status.HTTP_201_CREATED)
def create(obj_in: CloseReasonCreate, db: Session = Depends(get_db)):
    return CloseReasonService(db).create(obj_in)


@router.put("/{reason_id}", response_model=CloseReasonOut)
def update(reason_id: int, obj_in: CloseReasonUpdate, db: Session = Depends(get_db)):
    updated = CloseReasonService(db).update(reason_id, obj_in)
    if not updated:
        raise HTTPException(404, "Close reason not found")
    return updated


@router.delete("/{reason_id}", response_model=dict)
def delete(reason_id: int, db: Session = Depends(get_db)):
    deleted = CloseReasonService(db).delete(reason_id)
    if not deleted:
        raise HTTPException(404, "Close reason not found")
    return {"detail": "Close reason deactivated"}
