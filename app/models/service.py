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
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))

    company = relationship("Company", back_populates="services")
    tickets = relationship("Ticket", back_populates="service", cascade="all, delete")
