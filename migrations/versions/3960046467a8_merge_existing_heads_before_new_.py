"""merge existing heads before new migration

Revision ID: 3960046467a8
Revises: add_issued_by_to_issued_equipment, merge_heads
Create Date: 2026-01-20 09:19:17.079110

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3960046467a8'
down_revision = ('add_issued_by_to_issued_equipment', 'merge_heads')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
