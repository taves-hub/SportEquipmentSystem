from app import create_app, db
from models import AccessLog

def migrate_access_logs():
    """Migrate existing access_logs table to include new comprehensive fields"""

    app = create_app()
    with app.app_context():
        print("Starting AccessLog table migration...")

        try:
            # Check if new columns exist, if not add them
            from sqlalchemy import text

            # Get database connection
            connection = db.engine.connect()

            # Check existing columns
            result = connection.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'access_logs'
                AND table_schema = 'public'
            """))

            existing_columns = [row[0] for row in result]

            print(f"Existing columns: {existing_columns}")

            # List of new columns to add
            new_columns = [
                ("full_name", "VARCHAR(120)"),
                ("timezone", "VARCHAR(10) DEFAULT 'UTC'"),
                ("user_agent", "TEXT"),
                ("geolocation", "VARCHAR(255)"),
                ("action_status", "VARCHAR(20) DEFAULT 'Success'"),
                ("auth_method", "VARCHAR(50) DEFAULT 'password'"),
                ("session_id", "VARCHAR(255)"),
                ("login_attempts", "INTEGER DEFAULT 0"),
                ("mfa_used", "BOOLEAN DEFAULT FALSE"),
                ("app_name", "VARCHAR(100) DEFAULT 'SportEquipmentSystem'"),
                ("module", "VARCHAR(100)"),
                ("server_hostname", "VARCHAR(255)"),
                ("protocol", "VARCHAR(10) DEFAULT 'HTTP'"),
                ("data_changed", "TEXT"),
                ("record_id", "VARCHAR(100)"),
                ("query_executed", "TEXT"),
                ("access_level", "VARCHAR(50)"),
                ("alerts_triggered", "TEXT"),
                ("log_hash", "VARCHAR(128)"),
                ("retention_days", "INTEGER DEFAULT 365"),
                ("duration_ms", "INTEGER"),
                ("data_size_bytes", "INTEGER"),
                ("referrer_url", "VARCHAR(500)"),
                ("is_tamper_proof", "BOOLEAN DEFAULT TRUE"),
                ("search_index", "TEXT")
            ]

            # Add missing columns
            for column_name, column_type in new_columns:
                if column_name not in existing_columns:
                    print(f"Adding column: {column_name}")
                    try:
                        connection.execute(text(f"ALTER TABLE access_logs ADD COLUMN {column_name} {column_type}"))
                        print(f"✓ Added column: {column_name}")
                    except Exception as e:
                        print(f"✗ Failed to add column {column_name}: {str(e)}")

            connection.commit()
            connection.close()

            print("✅ AccessLog table migration completed successfully!")

            # Update existing records with default values
            print("Updating existing records with default values...")

            # Update timezone for existing records
            AccessLog.query.filter(AccessLog.timezone.is_(None)).update({
                'timezone': 'UTC',
                'action_status': 'Success',
                'auth_method': 'password',
                'app_name': 'SportEquipmentSystem',
                'protocol': 'HTTP',
                'retention_days': 365,
                'is_tamper_proof': True
            })

            # Generate hashes for existing records
            existing_logs = AccessLog.query.filter(AccessLog.log_hash.is_(None)).all()
            for log in existing_logs:
                log.log_hash = log.generate_log_hash()

            db.session.commit()
            print(f"✅ Updated {len(existing_logs)} existing records")

        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    migrate_access_logs()