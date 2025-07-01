# app/services/derivation_service.py
# --- ARCHIVO NUEVO ---
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.ticket import Ticket
from app.models.service import Service

class DerivationService:
    """
    Servicio para manejar la lógica de negocio de la derivación de tickets.
    """
    def __init__(self, db: Session):
        self.db = db

    def derive(self, ticket_id: int, new_service_id: int, deriving_user_id: int, company_id: int) -> Ticket:
        """
        Deriva un ticket a un nuevo servicio.
        """
        # 1. Validar el ticket
        ticket_to_derive = self.db.query(Ticket).filter(
            Ticket.id == ticket_id,
            Ticket.company_id == company_id
        ).first()

        if not ticket_to_derive:
            raise HTTPException(status_code=404, detail="Ticket no encontrado.")

        if ticket_to_derive.status not in ['pagado', 'en_atencion', 'esperando']:
             raise HTTPException(status_code=400, detail=f"No se puede derivar un ticket con estado '{ticket_to_derive.status}'.")

        # 2. Validar el nuevo servicio
        new_service = self.db.query(Service).filter(
            Service.id == new_service_id,
            Service.company_id == company_id,
            Service.is_active == True
        ).first()

        if not new_service:
            raise HTTPException(status_code=400, detail="El servicio de destino no es válido o está inactivo.")
            
        if new_service.id == ticket_to_derive.service_id:
            raise HTTPException(status_code=400, detail="No se puede derivar un ticket al mismo servicio.")

        # 3. Aplicar la lógica de derivación
        # Guardar el servicio original si es la primera derivación
        if ticket_to_derive.derivation_count == 0:
            ticket_to_derive.original_service_id = ticket_to_derive.service_id

        ticket_to_derive.service_id = new_service.id
        ticket_to_derive.status = 'derivado' # Nuevo estado para la cola de atención
        ticket_to_derive.derivation_count += 1
        ticket_to_derive.priority_level = 99  # Prioridad máxima para ser atendido rápidamente
        
        self.db.commit()
        self.db.refresh(ticket_to_derive)

        # Aquí se podría emitir un evento WebSocket para mover el ticket de cola en el display
        
        return ticket_to_derive