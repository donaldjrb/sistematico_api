from sqlalchemy.orm import Session

from app.models import Company
from app.schemas.company import CompanyCreate


class CompanyService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Company).filter_by(is_active=True).all()

    def get(self, company_id: int):
        return self.db.query(Company).filter_by(id=company_id, is_active=True).first()

    def create(self, obj_in: CompanyCreate):
        new_company = Company(**obj_in.model_dump())
        self.db.add(new_company)
        self.db.commit()
        self.db.refresh(new_company)
        return new_company

    def update(self, company_id: int, obj_in: CompanyCreate):
        db_obj = self.get(company_id)
        if not db_obj:
            return None
        for field, value in obj_in.model_dump().items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, company_id: int):
        db_obj = self.get(company_id)
        if not db_obj:
            return None
        db_obj.is_active = False
        self.db.commit()
        return db_obj
