from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), nullable=False)
    priority_level = Column(Integer, default=0)
    status = Column(String(20), default="esperando")
    call_count = Column(Integer, default=0)
    customer_phone = Column(String(30), nullable=True)

    close_reason_id = Column(
        Integer,
        ForeignKey("close_reasons.id", ondelete="SET NULL"),
        nullable=True,
    )
    close_notes = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"))

    # ─── Relaciones ───────────────────────────────────────────────────────────
    company = relationship("Company", back_populates="tickets")
    service = relationship("Service", back_populates="tickets")
    close_reason = relationship("CloseReason", back_populates="tickets")

