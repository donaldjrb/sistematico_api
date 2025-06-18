from typing import Optional

from pydantic import BaseModel, HttpUrl


class MediaFileBase(BaseModel):
    description: Optional[str] = None
    file_url: HttpUrl
    media_type: str
    is_active: bool = True
    company_id: int


class MediaFileCreate(MediaFileBase):
    pass


class MediaFileUpdate(BaseModel):
    description: Optional[str]
    file_url: Optional[HttpUrl]
    media_type: Optional[str]
    is_active: Optional[bool]


class MediaFileOut(MediaFileBase):
    id: int
    model_config = {"from_attributes": True}
