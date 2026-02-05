"""Add document_path to campus_distributions table"""
from alembic import op
import sqlalchemy as sa


revision = 'add_document_path_002'
down_revision = 'campus_distribution_001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('campus_distributions', 
                  sa.Column('document_path', sa.String(500), nullable=True))


def downgrade():
    op.drop_column('campus_distributions', 'document_path')
