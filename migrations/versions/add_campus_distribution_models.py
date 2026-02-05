"""Add SatelliteCampus, EquipmentCategory, and CampusDistribution models

Revision ID: campus_distribution_001
Revises: 
Create Date: 2026-01-30 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'campus_distribution_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create satellite_campuses table
    op.create_table(
        'satellite_campuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create equipment_categories table
    op.create_table(
        'equipment_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_code', sa.String(10), nullable=False, unique=True),
        sa.Column('category_name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create campus_distributions table
    op.create_table(
        'campus_distributions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campus_id', sa.Integer(), nullable=False),
        sa.Column('equipment_id', sa.Integer(), nullable=False),
        sa.Column('category_code', sa.String(10), nullable=False),
        sa.Column('category_name', sa.String(100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('date_distributed', sa.DateTime(), nullable=True),
        sa.Column('distributed_by', sa.String(120), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['campus_id'], ['satellite_campuses.id'], ),
        sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('campus_distributions')
    op.drop_table('equipment_categories')
    op.drop_table('satellite_campuses')
