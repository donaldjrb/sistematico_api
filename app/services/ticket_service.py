# app/services/ticket_service.py
# --- MODIFICADO ---
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

# Se importa el modelo Service para poder consultarlo
from app.models.ticket import Ticket
from app.models.service import Service
from app.schemas.ticket import TicketCreate


class TicketService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        # Este método se deberá ajustar más adelante para las diferentes colas (Caja, Atención, etc.)
        # Por ahora, sigue devolviendo la cola original.
        return self.db.query(Ticket).filter(Ticket.status == "esperando").all()

    def get(self, ticket_id: int):
        return self.db.query(Ticket).filter_by(id=ticket_id).first()

    def create(self, obj_in: TicketCreate, company_id: int):
        # --- INICIO DE LÓGICA DE CREACIÓN EXTENDIDA ---
        
        # 1. Obtener el servicio para verificar si es válido y si requiere pago
        service = self.db.query(Service).filter(
            Service.id == obj_in.service_id, 
            Service.company_id == company_id
        ).first()

        if not service:
            # Usamos HTTPException aquí para que el endpoint pueda devolver un error claro.
            raise HTTPException(status_code=404, detail="El servicio especificado no existe o no pertenece a esta compañía.")

        if not service.is_active:
            raise HTTPException(status_code=400, detail="No se pueden generar tickets para un servicio inactivo.")

        # 2. Determinar el estado inicial del ticket
        initial_status = "pendiente_pago" if service.requires_payment else "esperando"

        # 3. Generar un número de ticket (usando la lógica que ya tenías)
        # Se asume que quieres un correlativo por compañía y no por servicio para evitar duplicados.
        ticket_count_today = self.db.query(Ticket).filter(
            Ticket.company_id == company_id,
            func.date(Ticket.created_at) == func.date(func.now())
        ).count()
        new_ticket_number = f"{service.code}-{ticket_count_today + 1:04d}"

        # 4. Crear el objeto Ticket con los datos calculados
        new_ticket = Ticket(
            ticket_number=new_ticket_number,
            status=initial_status,
            priority_level=service.priority_level,
            company_id=company_id,
            service_id=obj_in.service_id,
            customer_phone=obj_in.customer_phone
        )
        
        self.db.add(new_ticket)
        self.db.commit()
        self.db.refresh(new_ticket)
        return new_ticket
        # --- FIN DE LÓGICA DE CREACIÓN EXTENDIDA ---

    def update(self, ticket_id: int, obj_in: dict):
        db_obj = self.get(ticket_id)
        if not db_obj:
            return None
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, ticket_id: int):
        db_obj = self.get(ticket_id)
        if not db_obj:
            return None
        # Esta acción ahora se considera 'cerrar' un ticket.
        db_obj.status = "cerrado"
        self.db.commit()
        return db_obj
