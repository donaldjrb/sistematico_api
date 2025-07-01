# app/models/service.py
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.db.session import Base 

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10))
    location = Column(String(100))
    max_capacity = Column(Integer, default=0)
    priority_level = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    requires_payment = Column(Boolean, default=False, nullable=False)
    
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    # Relación existente con Company
    company = relationship("Company", back_populates="services")
    
    # Relación existente con Ticket
    tickets = relationship("Ticket", back_populates="service", foreign_keys="[Ticket.service_id]")

    # --- INICIO DE MODIFICACIÓN QUIRÚRGICA ---
    # Se añade la relación inversa para conectar los servicios con los usuarios.
    # Esto permite que SQLAlchemy sepa qué usuarios pertenecen a este servicio.
    users = relationship("User", back_populates="service")
    # --- FIN DE MODIFICACIÓN QUIRÚRGICA ---
