from pydantic import BaseModel, EmailStr


class CompanyCreate(BaseModel):
    name: str
    email: EmailStr
    country: str | None = None
    tax_id_name: str | None = None
    tax_id_value: str | None = None
    address: str | None = None
    phone_number: str | None = None
    logo_url: str | None = None
    contact_person: str | None = None


class CompanyOut(CompanyCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
