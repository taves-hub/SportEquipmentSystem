#!/usr/bin/env python
"""Add document_path column to campus_distributions table"""
import os
import sys
from sqlalchemy import create_engine, text

# Database configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'sports_equipment_db')

# Create connection string
if DB_PASSWORD:
    connection_string = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
else:
    connection_string = f'mysql+pymysql://{DB_USER}@{DB_HOST}/{DB_NAME}'

try:
    engine = create_engine(connection_string)
    
    with engine.connect() as connection:
        # Check if column already exists
        result = connection.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME='campus_distributions' AND COLUMN_NAME='document_path'
        """))
        
        if result.fetchone():
            print("✓ Column 'document_path' already exists in campus_distributions table")
        else:
            # Add the column
            connection.execute(text(
                'ALTER TABLE campus_distributions ADD COLUMN document_path VARCHAR(500) NULL'
            ))
            connection.commit()
            print("✓ Column 'document_path' added successfully to campus_distributions table")
            
except Exception as e:
    print(f"✗ Error: {e}", file=sys.stderr)
    sys.exit(1)
