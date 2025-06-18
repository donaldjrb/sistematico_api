from typing import Optional

from pydantic import BaseModel


# ----- base común -----
class CloseReasonBase(BaseModel):
    reason_text: str
    is_active: bool = True
    company_id: int


# ----- entrada -----
class CloseReasonCreate(CloseReasonBase):
    pass


class CloseReasonUpdate(BaseModel):
    reason_text: Optional[str]
    is_active: Optional[bool]


# ----- salida -----
class CloseReasonOut(CloseReasonBase):
    id: int

    class Config:
        from_attributes = True
