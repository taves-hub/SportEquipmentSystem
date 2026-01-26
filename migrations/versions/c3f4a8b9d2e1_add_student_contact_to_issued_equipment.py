"""add student contact fields to issued_equipment

Revision ID: c3f4a8b9d2e1
Revises: 79d53238989b
Create Date: 2025-11-24 15:59:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f4a8b9d2e1'
down_revision = '79d53238989b'
branch_labels = None
depends_on = None


def upgrade():
    # Add student_email and student_phone to issued_equipment
    with op.batch_alter_table('issued_equipment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('student_email', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('student_phone', sa.String(length=15), nullable=True))


def downgrade():
    # Remove the columns on downgrade
    with op.batch_alter_table('issued_equipment', schema=None) as batch_op:
        batch_op.drop_column('student_phone')
        batch_op.drop_column('student_email')
