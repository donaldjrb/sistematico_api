from typing import Optional

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    full_name: str
    email: EmailStr
    role: str = "agent"
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str]
    email: Optional[EmailStr]
    role: Optional[str]
    is_active: Optional[bool]


class UserOut(UserBase):
    id: int
    company_id: int

    class Config:
        from_attributes = True
