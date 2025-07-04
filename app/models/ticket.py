# app/models/ticket.py
import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import CHAR

from app.db.session import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    
    # --- INICIO DE MODIFICACIÓN ---
    # Se añade un campo UUID para la identificación pública y segura del ticket.
    # Se utiliza CHAR(36) para almacenar el UUID como una cadena.
    uuid = Column(CHAR(36), unique=True, index=True, nullable=False, default=lambda: str(uuid.uuid4()))
    # --- FIN DE MODIFICACIÓN ---
    
    ticket_number = Column(String(20), nullable=False)
    priority_level = Column(Integer, default=0)
    status = Column(String(50), default="esperando") 
    customer_phone = Column(String(30), nullable=True)
    close_notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    close_reason_id = Column(Integer, ForeignKey("close_reasons.id"), nullable=True)
    
    call_count = Column(Integer, default=0, nullable=False)
    attended_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Mantenemos sus campos existentes
    original_service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    derivation_count = Column(Integer, default=0, nullable=False)
    processed_by_cashier_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # --- RELACIONES ---
    company = relationship("Company")
    service = relationship("Service", foreign_keys=[service_id])
    close_reason = relationship("CloseReason")

    attended_by = relationship("User", back_populates="attended_tickets", foreign_keys=[attended_by_id])

    original_service = relationship("Service", foreign_keys=[original_service_id])
    cashier = relationship("User", back_populates="processed_tickets_as_cashier", foreign_keys=[processed_by_cashier_id])


