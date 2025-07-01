from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

# Corregido para usar tu estructura existente
from app.db.session import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    country = Column(String(60))
    tax_id_name = Column(String(40))
    tax_id_value = Column(String(30), unique=True)
    address = Column(String(120))
    phone_number = Column(String(30))
    email = Column(String(120), unique=True)
    logo_url = Column(String(255))
    contact_person = Column(String(100))
    is_active = Column(Boolean, default=True)

    # --- Relaciones Inversas Completas ---
    users = relationship("User", back_populates="company", cascade="all, delete")
    services = relationship("Service", back_populates="company", cascade="all, delete")
    tickets = relationship("Ticket", back_populates="company", cascade="all, delete")
    advertisements = relationship("Advertisement", back_populates="company", cascade="all, delete")
    close_reasons = relationship("CloseReason", back_populates="company", cascade="all, delete")
    media_files = relationship("MediaFile", back_populates="company", cascade="all, delete")


