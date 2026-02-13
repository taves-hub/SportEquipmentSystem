"""empty message

Revision ID: 285be9df0a73
Revises: damage_clearance_001, add_document_path_002, add_storekeeper_approval
Create Date: 2026-02-13 10:16:03.582608

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '285be9df0a73'
down_revision = ('damage_clearance_001', 'add_document_path_002', 'add_storekeeper_approval')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
