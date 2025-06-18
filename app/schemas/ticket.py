from datetime import datetime

from pydantic import BaseModel


class TicketCreate(BaseModel):
    ticket_number: str
    priority_level: int = 0
    customer_phone: str | None = None
    close_reason_id: int | None = None
    close_notes: str | None = None
    company_id: int
    service_id: int


class TicketOut(TicketCreate):
    id: int
    status: str
    call_count: int
    created_at: datetime
    updated_at: datetime | None

    class Config:
        from_attributes = True
