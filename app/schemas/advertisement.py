from typing import Optional

from pydantic import BaseModel


class AdvertisementBase(BaseModel):
    description: Optional[str] = None
    is_active: bool = True
    company_id: int


class AdvertisementCreate(AdvertisementBase):
    pass


class AdvertisementUpdate(BaseModel):
    description: Optional[str]
    is_active: Optional[bool]


class AdvertisementOut(AdvertisementBase):
    id: int
    model_config = {"from_attributes": True}  # pydantic v2
