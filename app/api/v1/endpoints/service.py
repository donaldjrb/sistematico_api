from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.service import ServiceCreate, ServiceOut
from app.services.service_service import ServiceService

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/", response_model=List[ServiceOut])
def read_all(db: Session = Depends(get_db)):
    return ServiceService(db).get_all()


@router.get("/{service_id}", response_model=ServiceOut)
def read_one(service_id: int, db: Session = Depends(get_db)):
    svc = ServiceService(db).get(service_id)
    if not svc:
        raise HTTPException(status_code=404, detail="Service not found")
    return svc


@router.post("/", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
def create(obj_in: ServiceCreate, db: Session = Depends(get_db)):
    return ServiceService(db).create(obj_in)


@router.put("/{service_id}", response_model=ServiceOut)
def update(service_id: int, obj_in: ServiceCreate, db: Session = Depends(get_db)):
    updated = ServiceService(db).update(service_id, obj_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Service not found")
    return updated


@router.delete("/{service_id}", response_model=dict)
def delete(service_id: int, db: Session = Depends(get_db)):
    deleted = ServiceService(db).delete(service_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Service not found")
    return {"detail": "Service disabled"}
