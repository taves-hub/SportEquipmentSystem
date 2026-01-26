import os, sys
# ensure project root is on sys.path so imports like `app` and `extensions` work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    conn = db.engine.connect()
    try:
        db_name = conn.execute(text('SELECT DATABASE()')).scalar()
        print(f"Current database: {db_name}")

        check = conn.execute(
            text("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = :schema AND TABLE_NAME = 'equipment' AND COLUMN_NAME = 'is_active'"),
            {"schema": db_name}
        ).scalar()

        if check and int(check) > 0:
            print('Column is_active already exists in equipment table.')
        else:
            print('Adding is_active column to equipment table...')
            conn.execute(text("ALTER TABLE equipment ADD COLUMN is_active TINYINT(1) NOT NULL DEFAULT 1"))
            print('Column added successfully.')
    except Exception as e:
        print('Error while modifying database:', e)
    finally:
        conn.close()
