from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.session import Base


class MediaFile(Base):
    __tablename__ = "media_files"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String(255))
    file_url = Column(String(255))
    media_type = Column(String(30))
    is_active = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))

    company = relationship("Company")
