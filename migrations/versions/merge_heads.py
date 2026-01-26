"""
Merge multiple heads into a single revision
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'merge_heads'
down_revision = ('remove_unique_category_code', 'add_staff_fields_to_issued_equipment')
branch_labels = None
depends_on = None

def upgrade():
    # This is a merge revision, no DB schema changes
    pass

def downgrade():
    pass
