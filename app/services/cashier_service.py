# app/services/cashier_service.py
# --- ARCHIVO NUEVO ---
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List

from app.models.ticket import Ticket
from app.models.user import User

class CashierService:
    """
    Servicio para manejar la lógica de negocio de la caja.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_pending_for_payment(self, company_id: int) -> List[Ticket]:
        """
        Obtiene todos los tickets con estado 'pendiente_pago' para una compañía específica.
        """
        return self.db.query(Ticket).filter(
            Ticket.company_id == company_id,
            Ticket.status == 'pendiente_pago'
        ).order_by(Ticket.created_at.asc()).all()

    def process_payment(self, ticket_id: int, cashier_user_id: int, company_id: int) -> Ticket:
        """
        Procesa el pago de un ticket, cambiando su estado a 'pagado'.
        """
        ticket_to_pay = self.db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.company_id == company_id
        ).first()

        if not ticket_to_pay:
            raise HTTPException(status_code=404, detail="Ticket no encontrado o no pertenece a esta compañía.")

        if ticket_to_pay.status != 'pendiente_pago':
            raise HTTPException(status_code=400, detail=f"El ticket no está pendiente de pago. Su estado actual es: '{ticket_to_pay.status}'.")

        ticket_to_pay.status = 'pagado'
        ticket_to_pay.processed_by_cashier_id = cashier_user_id
        
        self.db.commit()
        self.db.refresh(ticket_to_pay)
        
        # Aquí se podría emitir un evento WebSocket para notificar a los agentes de atención
        
        return ticket_to_pay