"""remove unique constraint on equipment.category_code

Revision ID: remove_unique_category_code
Revises: c3f4a8b9d2e1
Create Date: 2025-11-25 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_unique_category_code'
down_revision = 'c3f4a8b9d2e1'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the unique index on category_code so multiple equipment rows
    # can share the same category_code (we use category_code+name at app level).
    with op.batch_alter_table('equipment', schema=None) as batch_op:
        batch_op.drop_index('category_code')


def downgrade():
    # Recreate the unique index on category_code (reverse of upgrade).
    with op.batch_alter_table('equipment', schema=None) as batch_op:
        batch_op.create_index('category_code', ['category_code'], unique=True)