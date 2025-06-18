from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.company import CompanyCreate, CompanyOut
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=List[CompanyOut])
def read_all(db: Session = Depends(get_db)):
    return CompanyService(db).get_all()


@router.get("/{company_id}", response_model=CompanyOut)
def read_one(company_id: int, db: Session = Depends(get_db)):
    company = CompanyService(db).get(company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return company


@router.post("/", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
def create_company(obj_in: CompanyCreate, db: Session = Depends(get_db)):
    return CompanyService(db).create(obj_in)


@router.put("/{company_id}", response_model=CompanyOut)
def update_company(
    company_id: int, obj_in: CompanyCreate, db: Session = Depends(get_db)
):
    updated = CompanyService(db).update(company_id, obj_in)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return updated


@router.delete("/{company_id}", response_model=dict)
def delete_company(company_id: int, db: Session = Depends(get_db)):
    deleted = CompanyService(db).delete(company_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Company not found"
        )
    return {"detail": "Company disabled"}
