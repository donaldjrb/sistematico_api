from pydantic import BaseModel


class ServiceCreate(BaseModel):
    name: str
    code: str | None = None
    location: str | None = None
    max_capacity: int = 0
    priority_level: int = 0
    company_id: int


class ServiceOut(ServiceCreate):
    id: int
    is_active: bool

    class Config:
        from_attributes = True
