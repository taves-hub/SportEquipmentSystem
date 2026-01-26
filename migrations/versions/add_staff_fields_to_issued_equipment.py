"""
Alembic migration to add staff fields to issued_equipment table
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_staff_fields_to_issued_equipment'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('issued_equipment', sa.Column('staff_payroll', sa.String(20), nullable=True))
    op.add_column('issued_equipment', sa.Column('staff_name', sa.String(100), nullable=True))
    op.add_column('issued_equipment', sa.Column('staff_email', sa.String(120), nullable=True))

def downgrade():
    op.drop_column('issued_equipment', 'staff_payroll')
    op.drop_column('issued_equipment', 'staff_name')
    op.drop_column('issued_equipment', 'staff_email')
