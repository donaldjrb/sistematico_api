"""Add uuid to Ticket model for public access

Revision ID: cea57c021533
Revises: fff4743cff36
Create Date: 2025-07-01 20:39:56.478792

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import uuid # Se importa la librería para generar UUIDs


# revision identifiers, used by Alembic.
revision: str = 'cea57c021533'
down_revision: Union[str, Sequence[str], None] = 'fff4743cff36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### INICIO DE LA CORRECCIÓN MANUAL ###

    # Paso 1: Añadir la nueva columna 'uuid', permitiendo que sea nula temporalmente.
    op.add_column('tickets', sa.Column('uuid', sa.CHAR(36), nullable=True))

    # Paso 2: Generar y asignar un UUID único para cada ticket existente.
    conn = op.get_bind()
    tickets_to_update = conn.execute(sa.text("SELECT id FROM tickets WHERE uuid IS NULL")).fetchall()

    for ticket in tickets_to_update:
        ticket_id = ticket[0]
        new_uuid = str(uuid.uuid4())
        conn.execute(
            sa.text("UPDATE tickets SET uuid = :uuid WHERE id = :id"),
            {"uuid": new_uuid, "id": ticket_id}
        )

    # Paso 3: Ahora que todos los tickets tienen un UUID, se modifica la columna
    # para que sea obligatoria (NOT NULL) y se crea el índice único.
    op.alter_column('tickets', 'uuid',
               existing_type=sa.CHAR(36),
               nullable=False)
    
    op.create_index(op.f('ix_tickets_uuid'), 'tickets', ['uuid'], unique=True)
    
    # ### FIN DE LA CORRECCIÓN MANUAL ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### El downgrade se mantiene igual ###
    op.drop_index(op.f('ix_tickets_uuid'), table_name='tickets')
    op.drop_column('tickets', 'uuid')
    # ### end Alembic commands ###
