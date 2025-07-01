# app/schemas/ticket.py 

from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class TicketBase(BaseModel):
    service_id: int
    customer_phone: Optional[str] = None

class TicketCreate(TicketBase):
    # ticket_number y priority_level se generarán en el servicio
    pass

class TicketUpdate(BaseModel):
    status: Optional[str] = None
    close_notes: Optional[str] = None
    close_reason_id: Optional[int] = None

class TicketDerive(BaseModel):
    new_service_id: int

# --- INICIO DE CORRECCIÓN QUIRÚRGICA ---
# Se ha confirmado que el campo `call_count` ya existe en tu esquema `TicketOut`.
# El esquema ya está listo para la nueva funcionalidad. No se requieren más cambios aquí.
# Sin embargo, para mantener la consistencia con el modelo, nos aseguraremos de que
# todos los campos del modelo Ticket estén presentes.
class TicketOut(TicketBase):
    id: int
    ticket_number: str
    priority_level: int
    status: str
    call_count: int # Este campo ya estaba, lo cual es perfecto.
    created_at: datetime
    updated_at: Optional[datetime] = None
    company_id: int
    
    class Config:
        from_attributes = True
# --- FIN DE CORRECCIÓN QUIRÚRGICA ---
