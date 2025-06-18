from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.media_file import MediaFile
from app.schemas.media_file import MediaFileCreate, MediaFileUpdate


class MediaFileService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self) -> List[MediaFile]:
        return self.db.query(MediaFile).all()

    def get(self, mf_id: int) -> Optional[MediaFile]:
        return self.db.query(MediaFile).filter(MediaFile.id == mf_id).first()

    def create(self, obj_in: MediaFileCreate) -> MediaFile:
        db_mf = MediaFile(**obj_in.dict())
        self.db.add(db_mf)
        self.db.commit()
        self.db.refresh(db_mf)
        return db_mf

    def update(self, mf_id: int, obj_in: MediaFileUpdate) -> Optional[MediaFile]:
        mf = self.get(mf_id)
        if not mf:
            return None
        for f, v in obj_in.dict(exclude_unset=True).items():
            setattr(mf, f, v)
        self.db.commit()
        self.db.refresh(mf)
        return mf

    def delete(self, mf_id: int) -> bool:
        mf = self.get(mf_id)
        if not mf:
            return False
        mf.is_active = False
        self.db.commit()
        return True
