import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base

class MediaFile(Base):
    """
    Represents a multimedia file (image or video) for the display.
    """
    __tablename__ = 'media_files'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    
    # Foreign key to the company that owns this file.
    company_id = sa.Column(sa.Integer, sa.ForeignKey('companies.id'), nullable=False, index=True)
    
    # Descriptive name for the file, e.g., "Promo Verano 2025".
    name = sa.Column(sa.String(255), nullable=False)
    
    # Type of the file, e.g., "image" or "video".
    file_type = sa.Column(sa.String(50), nullable=False)
    
    # URL path to access the file, e.g., "/static/media/1/promo.mp4".
    url = sa.Column(sa.String(512), nullable=False)
    
    # Status to control if the file is active on the display.
    status = sa.Column(sa.Boolean, default=True, nullable=False)
    
    # Timestamp of when the file was created/uploaded.
    date_create = sa.Column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Duration in seconds the file should be displayed.
    # For images, this is user-defined.
    # For videos, this can be auto-detected upon upload.
    duration_seconds = sa.Column(sa.Integer, nullable=False, default=10)

    # Relationship to the Company model.
    company = relationship("Company")
