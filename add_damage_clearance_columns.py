#!/usr/bin/env python
"""Script to add damage clearance columns to issued_equipment table"""

import sys
sys.path.insert(0, 'c:\\xampp\\htdocs\\SportEquipmentSystem')

from app import create_app
from extensions import db

app = create_app()
with app.app_context():
    # Add the new columns to issued_equipment table
    try:
        db.session.execute(db.text("""
            ALTER TABLE issued_equipment 
            ADD COLUMN IF NOT EXISTS damage_clearance_status VARCHAR(50) DEFAULT NULL,
            ADD COLUMN IF NOT EXISTS damage_clearance_notes TEXT DEFAULT NULL
        """))
        db.session.commit()
        print("✓ Database migration successful - columns added")
    except Exception as e:
        print(f"Note: {str(e)}")
        db.session.rollback()
