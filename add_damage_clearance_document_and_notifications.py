#!/usr/bin/env python
"""Script to add damage_clearance_document column and notifications table to the database.

This mirrors the project's approach when Alembic isn't configured.
"""
import sys
sys.path.insert(0, 'c:\\xampp\\htdocs\\SportEquipmentSystem')

from app import create_app
from extensions import db

app = create_app()
with app.app_context():
    try:
        # Add column to issued_equipment if not exists (best-effort)
        db.session.execute(db.text("""
            ALTER TABLE issued_equipment
            ADD COLUMN IF NOT EXISTS damage_clearance_document VARCHAR(500) DEFAULT NULL
        """))
        # Create notifications table if it doesn't exist
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                recipient_role VARCHAR(20) NOT NULL,
                recipient_id INT,
                message LONGTEXT NOT NULL,
                url VARCHAR(500),
                is_read BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        db.session.commit()
        print("✓ Database changes applied: column + notifications table (if supported)")
    except Exception as e:
        print(f"Note: {str(e)}")
        db.session.rollback()
