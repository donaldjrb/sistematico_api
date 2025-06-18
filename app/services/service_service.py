from sqlalchemy.orm import Session

from app.models import Service
from app.schemas.service import ServiceCreate


class ServiceService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Service).filter_by(is_active=True).all()

    def get(self, service_id: int):
        return self.db.query(Service).filter_by(id=service_id, is_active=True).first()

    def create(self, obj_in: ServiceCreate):
        new_service = Service(**obj_in.model_dump())
        self.db.add(new_service)
        self.db.commit()
        self.db.refresh(new_service)
        return new_service

    def update(self, service_id: int, obj_in: ServiceCreate):
        db_obj = self.get(service_id)
        if not db_obj:
            return None
        for field, value in obj_in.model_dump().items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, service_id: int):
        db_obj = self.get(service_id)
        if not db_obj:
            return None
        db_obj.is_active = False
        self.db.commit()
        return db_obj
