"""
Simple helper to apply schema changes required by the return-condition feature.
This script runs ALTER TABLE statements to add the following columns if they are missing:
 - issued_equipment.return_conditions TEXT
 - issued_equipment.serial_numbers TEXT
 - equipment.damaged_count INT DEFAULT 0
 - equipment.lost_count INT DEFAULT 0

Run this with the same Python environment used by the app. It reads DB URI from `config.Config.SQLALCHEMY_DATABASE_URI`.
This is a fallback alternative to using Flask-Migrate.
"""
import pymysql
from urllib.parse import urlparse
from config import Config


def _parse_uri(uri):
    # expecting mysql+pymysql://user:pass@host/dbname
    if uri.startswith('mysql+pymysql://'):
        uri = uri.replace('mysql+pymysql://', '')
    parsed = urlparse('//' + uri)
    username = parsed.username or 'root'
    password = parsed.password or ''
    host = parsed.hostname or 'localhost'
    db = parsed.path.lstrip('/')
    return username, password, host, db


def apply():
    uri = Config.SQLALCHEMY_DATABASE_URI
    user, pwd, host, db = _parse_uri(uri)
    print(f"Connecting to {host}/{db} as {user}")
    try:
        conn = pymysql.connect(host=host, user=user, password=pwd, database=db)
        with conn.cursor() as cur:
            # issued_equipment.return_conditions (change from return_condition)
            try:
                cur.execute("ALTER TABLE issued_equipment CHANGE COLUMN return_condition return_conditions TEXT")
                print('Changed issued_equipment.return_condition to return_conditions TEXT')
            except Exception as e:
                print('Failed to change return_condition to return_conditions:', e)

            # issued_equipment.serial_numbers (change from serial_number)
            try:
                cur.execute("ALTER TABLE issued_equipment CHANGE COLUMN serial_number serial_numbers TEXT")
                print('Changed issued_equipment.serial_number to serial_numbers TEXT')
            except Exception as e:
                print('Failed to change serial_number to serial_numbers:', e)

            # equipment.damaged_count
            try:
                cur.execute("ALTER TABLE equipment ADD COLUMN damaged_count INT DEFAULT 0")
                print('Added equipment.damaged_count')
            except Exception as e:
                print('equipment.damaged_count already exists or failed to add:', e)

            # equipment.lost_count
            try:
                cur.execute("ALTER TABLE equipment ADD COLUMN lost_count INT DEFAULT 0")
                print('Added equipment.lost_count')
            except Exception as e:
                print('equipment.lost_count already exists or failed to add:', e)

            # equipment.serial_number (add column if missing)
            try:
                cur.execute("ALTER TABLE equipment ADD COLUMN serial_number VARCHAR(100)")
                print('Added equipment.serial_number')
            except Exception as e:
                print('equipment.serial_number already exists or failed to add:', e)

            # Ensure every row has a serial_number to allow NOT NULL + UNIQUE
            try:
                cur.execute("UPDATE equipment SET serial_number = CONCAT('SN', id) WHERE serial_number IS NULL OR serial_number = ''")
                print('Filled missing serial_number values')
            except Exception as e:
                print('Failed to fill missing serial_number values:', e)

            # Make serial_number NOT NULL
            try:
                cur.execute("ALTER TABLE equipment MODIFY COLUMN serial_number VARCHAR(100) NOT NULL")
                print('Made equipment.serial_number NOT NULL')
            except Exception as e:
                print('Failed to set serial_number NOT NULL (might already be NOT NULL):', e)

            # Add unique index on serial_number
            try:
                cur.execute("CREATE UNIQUE INDEX ux_equipment_serial_number ON equipment (serial_number)")
                print('Added UNIQUE index on equipment.serial_number')
            except Exception as e:
                print('Failed to create unique index on serial_number (may already exist or duplicates present):', e)

        conn.commit()
        conn.close()
        print('Done')
    except Exception as e:
        print('Failed to apply migrations:', e)


if __name__ == '__main__':
    apply()
