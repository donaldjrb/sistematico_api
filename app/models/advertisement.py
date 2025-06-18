from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class Advertisement(Base):
    __tablename__ = "advertisements"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255))
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))

    company = relationship("Company")
