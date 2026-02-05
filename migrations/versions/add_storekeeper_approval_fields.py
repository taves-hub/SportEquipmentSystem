"""Add approval fields to StoreKeeper model

Revision ID: add_storekeeper_approval
Revises: 
Create Date: 2026-02-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_storekeeper_approval'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add is_approved column with default False
    op.add_column('storekeepers', sa.Column('is_approved', sa.Boolean(), nullable=False, server_default='0'))
    
    # Add approved_at column
    op.add_column('storekeepers', sa.Column('approved_at', sa.DateTime(), nullable=True))
    
    # Add created_at column
    op.add_column('storekeepers', sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()))


def downgrade():
    op.drop_column('storekeepers', 'created_at')
    op.drop_column('storekeepers', 'approved_at')
    op.drop_column('storekeepers', 'is_approved')
