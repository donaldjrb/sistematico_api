from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.advertisement import Advertisement
from app.schemas.advertisement import AdvertisementCreate, AdvertisementUpdate


class AdvertisementService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[Advertisement]:
        return self.db.query(Advertisement).all()

    def get(self, adv_id: int) -> Optional[Advertisement]:
        return self.db.query(Advertisement).filter(Advertisement.id == adv_id).first()

    def create(self, obj_in: AdvertisementCreate) -> Advertisement:
        db_adv = Advertisement(**obj_in.dict())
        self.db.add(db_adv)
        self.db.commit()
        self.db.refresh(db_adv)
        return db_adv

    def update(
        self, adv_id: int, obj_in: AdvertisementUpdate
    ) -> Optional[Advertisement]:
        adv = self.get(adv_id)
        if not adv:
            return None
        for f, v in obj_in.dict(exclude_unset=True).items():
            setattr(adv, f, v)
        self.db.commit()
        self.db.refresh(adv)
        return adv

    def delete(self, adv_id: int) -> bool:
        adv = self.get(adv_id)
        if not adv:
            return False
        adv.is_active = False
        self.db.commit()
        return True
