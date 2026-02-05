"""
Direct database migration script for storekeeper approval fields
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import StoreKeeper
from sqlalchemy import inspect

def run_migration():
    """Add approval fields to storekeepers table"""
    with app.app_context():
        # Get database inspector
        inspector = inspect(db.engine)
        columns = {col['name'] for col in inspector.get_columns('storekeepers')}
        
        print("Current columns in storekeepers table:", columns)
        
        # Check if columns already exist
        if 'is_approved' in columns:
            print("✓ is_approved column already exists")
        else:
            print("Adding is_approved column...")
            db.engine.execute('ALTER TABLE storekeepers ADD COLUMN is_approved BOOLEAN NOT NULL DEFAULT 0')
            print("✓ Added is_approved column")
        
        if 'approved_at' in columns:
            print("✓ approved_at column already exists")
        else:
            print("Adding approved_at column...")
            db.engine.execute('ALTER TABLE storekeepers ADD COLUMN approved_at DATETIME NULL')
            print("✓ Added approved_at column")
        
        if 'created_at' in columns:
            print("✓ created_at column already exists")
        else:
            print("Adding created_at column...")
            db.engine.execute('ALTER TABLE storekeepers ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP')
            print("✓ Added created_at column")
        
        print("\n✓ Migration completed successfully!")

if __name__ == '__main__':
    try:
        run_migration()
    except Exception as e:
        print(f"✗ Migration failed: {str(e)}")
        sys.exit(1)
