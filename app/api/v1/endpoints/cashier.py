from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.ticket import TicketOut
from app.services.cashier_service import CashierService

router = APIRouter()

@router.get("/pending", response_model=List[TicketOut])
def get_pending_tickets(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Obtiene la lista de tickets pendientes de pago para la compañía del usuario actual.
    """
    if not current_user:
        raise HTTPException(status_code=403, detail="Acceso denegado.")
        
    company_id = current_user.get("company_id")
    cashier_service = CashierService(db)
    return cashier_service.get_pending_for_payment(company_id)


@router.post("/tickets/{ticket_id}/process-payment", response_model=TicketOut)
def process_ticket_payment(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Marca un ticket como pagado.
    """
    if not current_user:
        raise HTTPException(status_code=403, detail="Acceso denegado.")
        
    company_id = current_user.get("company_id")
    # Asumiendo que el ID del usuario está disponible en el token
    user_id = current_user.get("user_id") # Asegúrate de que este campo exista en tu sesión
    
    cashier_service = CashierService(db)
    return cashier_service.process_payment(ticket_id, user_id, company_id)
