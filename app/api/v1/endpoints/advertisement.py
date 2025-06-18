from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.advertisement import (
    AdvertisementCreate,
    AdvertisementOut,
    AdvertisementUpdate,
)
from app.services.advertisement_service import AdvertisementService

router = APIRouter(prefix="/advertisements", tags=["advertisements"])


@router.get("/", response_model=List[AdvertisementOut])
def read_all(db: Session = Depends(get_db)):
    return AdvertisementService(db).get_all()


@router.get("/{adv_id}", response_model=AdvertisementOut)
def read_one(adv_id: int, db: Session = Depends(get_db)):
    adv = AdvertisementService(db).get(adv_id)
    if not adv:
        raise HTTPException(404, "Advertisement not found")
    return adv


@router.post("/", response_model=AdvertisementOut, status_code=status.HTTP_201_CREATED)
def create(obj_in: AdvertisementCreate, db: Session = Depends(get_db)):
    return AdvertisementService(db).create(obj_in)


@router.put("/{adv_id}", response_model=AdvertisementOut)
def update(adv_id: int, obj_in: AdvertisementUpdate, db: Session = Depends(get_db)):
    upd = AdvertisementService(db).update(adv_id, obj_in)
    if not upd:
        raise HTTPException(404, "Advertisement not found")
    return upd


@router.delete("/{adv_id}", response_model=dict)
def delete(adv_id: int, db: Session = Depends(get_db)):
    ok = AdvertisementService(db).delete(adv_id)
    if not ok:
        raise HTTPException(404, "Advertisement not found")
    return {"detail": "Advertisement deactivated"}
