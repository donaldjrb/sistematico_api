from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(10), default="agent")
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))

    company = relationship("Company", back_populates="users")
