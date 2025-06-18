from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.media_file import MediaFileCreate, MediaFileOut, MediaFileUpdate
from app.services.media_file_service import MediaFileService

router = APIRouter(prefix="/media-files", tags=["media_files"])


@router.get("/", response_model=List[MediaFileOut])
def read_all(db: Session = Depends(get_db)):
    return MediaFileService(db).get_all()


@router.get("/{mf_id}", response_model=MediaFileOut)
def read_one(mf_id: int, db: Session = Depends(get_db)):
    mf = MediaFileService(db).get(mf_id)
    if not mf:
        raise HTTPException(404, "Media file not found")
    return mf


@router.post("/", response_model=MediaFileOut, status_code=status.HTTP_201_CREATED)
def create(obj_in: MediaFileCreate, db: Session = Depends(get_db)):
    return MediaFileService(db).create(obj_in)


@router.put("/{mf_id}", response_model=MediaFileOut)
def update(mf_id: int, obj_in: MediaFileUpdate, db: Session = Depends(get_db)):
    upd = MediaFileService(db).update(mf_id, obj_in)
    if not upd:
        raise HTTPException(404, "Media file not found")
    return upd


@router.delete("/{mf_id}", response_model=dict)
def delete(mf_id: int, db: Session = Depends(get_db)):
    ok = MediaFileService(db).delete(mf_id)
    if not ok:
        raise HTTPException(404, "Media file not found")
    return {"detail": "Media file deactivated"}
