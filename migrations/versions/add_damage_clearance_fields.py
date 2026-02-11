"""Add damage clearance status fields to IssuedEquipment

Revision ID: damage_clearance_001
Revises: 3960046467a8
Create Date: 2026-02-06 11:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'damage_clearance_001'
down_revision = '3960046467a8'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to issued_equipment table
    op.add_column('issued_equipment', sa.Column('damage_clearance_status', sa.String(50), nullable=True))
    op.add_column('issued_equipment', sa.Column('damage_clearance_notes', sa.Text, nullable=True))


def downgrade():
    # Remove the added columns
    op.drop_column('issued_equipment', 'damage_clearance_notes')
    op.drop_column('issued_equipment', 'damage_clearance_status')
