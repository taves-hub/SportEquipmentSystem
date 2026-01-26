"""
Add issued_by column to issued_equipment
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_issued_by_to_issued_equipment'
down_revision = 'remove_unique_category_code'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('issued_equipment', sa.Column('issued_by', sa.String(120), nullable=True))


def downgrade():
    op.drop_column('issued_equipment', 'issued_by')
