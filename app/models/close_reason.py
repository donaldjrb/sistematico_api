from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class CloseReason(Base):
    __tablename__ = "close_reasons"

    id = Column(Integer, primary_key=True, index=True)
    reason_text = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))

    company = relationship("Company")
    tickets = relationship("Ticket", back_populates="close_reason")
