# app/api/v1/endpoints/ticket.py
# --- MODIFICADO ---
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

# Se importa la dependencia de seguridad para obtener la compañía
from app.api.deps import get_db, get_current_user 
from app.schemas.ticket import TicketCreate, TicketOut, TicketUpdate, TicketDerive
from app.services.ticket_service import TicketService
# Se importan los nuevos servicios que se crearán a continuación
from app.services.cashier_service import CashierService
from app.services.derivation_service import DerivationService

router = APIRouter(prefix="/tickets", tags=["tickets"])


# --- RUTA EXISTENTE (get_all) - MODIFICADA PARA SER MÁS FLEXIBLE ---
@router.get("/", response_model=List[TicketOut])
def read_all(
    status: Optional[str] = Query(None, description="Filtrar tickets por estado (e.g., 'esperando', 'pendiente_pago')"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene una lista de tickets, opcionalmente filtrada por estado.
    - Agentes de atención final verán: 'esperando', 'pagado', 'derivado'.
    - Agentes de caja verán: 'pendiente_pago'.
    """
    company_id = current_user.get("company_id")
    # La lógica de filtrado específica se manejará en los servicios correspondientes
    # Aquí solo exponemos un filtro genérico por ahora.
    # En un futuro, se podrían crear endpoints específicos como /queue/attention y /queue/cashier
    
    # Lógica de ejemplo simple:
    query = db.query(Ticket).filter(Ticket.company_id == company_id)
    if status:
        query = query.filter(Ticket.status == status)
        
    return query.order_by(Ticket.priority_level.desc(), Ticket.created_at.asc()).all()


# --- RUTA EXISTENTE (read_one) - SIN CAMBIOS ---
@router.get("/{ticket_id}", response_model=TicketOut)
def read_one(ticket_id: int, db: Session = Depends(get_db)):
    ticket = TicketService(db).get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


# --- RUTA EXISTENTE (create) - MODIFICADA PARA CONTEXTO DE COMPAÑÍA ---
@router.post("/", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    obj_in: TicketCreate, 
    db: Session = Depends(get_db),
    # La creación de tickets puede ser pública (tablet) o interna.
    # Si es pública, no habrá un 'current_user'. Necesitamos una forma de obtener el company_id.
    # SOLUCIÓN: La tablet de autoservicio debería tener un `company_id` configurado.
    # Por ahora, para la API, lo hacemos dependiente de un usuario autenticado.
    current_user: dict = Depends(get_current_user) 
):
    company_id = current_user.get("company_id")
    # La lógica de validación y asignación de estado ahora está en el servicio.
    return TicketService(db).create(obj_in, company_id)


# --- RUTA EXISTENTE (update) - MODIFICADA PARA SER MÁS GENÉRICA ---
@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int, 
    obj_in: TicketUpdate, # Se usa el schema de actualización
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    # Se asegura que el ticket pertenezca a la compañía del usuario
    ticket_service = TicketService(db)
    ticket = ticket_service.get(ticket_id)
    if not ticket or ticket.company_id != current_user.get("company_id"):
        raise HTTPException(status_code=404, detail="Ticket not found")

    # obj_in.model_dump(exclude_unset=True) envía solo los campos que se quieren cambiar
    updated = ticket_service.update(ticket_id, obj_in.model_dump(exclude_unset=True))
    return updated


# --- NUEVA RUTA PARA DERIVACIÓN ---
@router.post("/{ticket_id}/derive", response_model=TicketOut)
def derive_ticket(
    ticket_id: int,
    obj_in: TicketDerive,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Deriva un ticket a un nuevo servicio, dándole máxima prioridad."""
    derivation_service = DerivationService(db)
    user_id = current_user.get("id") # Asumiendo que el id del usuario está en el token
    company_id = current_user.get("company_id")
    
    try:
        derived_ticket = derivation_service.derive(
            ticket_id=ticket_id,
            new_service_id=obj_in.new_service_id,
            deriving_user_id=user_id,
            company_id=company_id
        )
        return derived_ticket
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
