from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

# Se usa tu estructura existente
from app.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default='agent')
    is_active = Column(Boolean(), default=True)
    
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)

    # --- INICIO DE MODIFICACIÓN ---
    # Columna para la relación con el servicio
    service_id = Column(Integer, ForeignKey("services.id", ondelete="SET NULL"), nullable=True)

    # Relación para acceder al servicio del usuario desde el código (ej. user.service)
    # Se añade la relación inversa que apuntará a la propiedad 'users' en el modelo Service
    service = relationship("Service", back_populates="users")
    # --- FIN DE MODIFICACIÓN ---

    # Tu relación existente con Company, se mantiene intacta.
    company = relationship("Company", back_populates="users", lazy="joined")
    
    # Se añade la relación inversa para los tickets atendidos.
    # Esto nos permitirá en el futuro saber cuántos tickets ha cerrado un agente.
    attended_tickets = relationship("Ticket", back_populates="attended_by", foreign_keys="[Ticket.attended_by_id]")
    
    # Se añade la relación para los tickets procesados por el cajero
    processed_tickets_as_cashier = relationship("Ticket", back_populates="cashier", foreign_keys="[Ticket.processed_by_cashier_id]")



