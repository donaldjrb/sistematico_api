import sqlalchemy as sa
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Asumo que la importación de Base es desde app.db.session, como en los otros modelos.
from app.db.session import Base

class Advertisement(Base):
    """
    Represents a text-based advertisement for the display's marquee.
    """
    __tablename__ = 'advertisements'

    id = sa.Column(sa.Integer, primary_key=True, index=True)
    
    # Foreign key to the company that owns this advertisement.
    company_id = sa.Column(sa.Integer, sa.ForeignKey('companies.id'), nullable=False, index=True)
    
    # The text content of the advertisement.
    description = sa.Column(sa.String(500), nullable=False)
    
    # Status to control if the advertisement is active.
    is_active = sa.Column(sa.Boolean, default=True, nullable=False)
    
    # Timestamp of creation.
    date_create = sa.Column(sa.DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to the Company model.
    company = relationship("Company")