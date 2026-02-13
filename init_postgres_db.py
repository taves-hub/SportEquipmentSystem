from app import create_app, db
from models import *
from sqlalchemy import text

def init_postgres_db():
    """Initialize PostgreSQL database with schema"""
    app = create_app()

    with app.app_context():
        print("Creating PostgreSQL tables...")
        try:
            db.create_all()
            print("✓ All tables created successfully")

            # Create indexes for better performance
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_issued_equipment_student_id ON issued_equipment (student_id)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_issued_equipment_staff_payroll ON issued_equipment (staff_payroll)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_issued_equipment_equipment_id ON issued_equipment (equipment_id)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_issued_equipment_status ON issued_equipment (status)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_equipment_category_code ON equipment (category_code)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_equipment_serial_number ON equipment (serial_number)'))
            db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON notifications (recipient_role, recipient_id)'))

            print("✓ Indexes created successfully")

        except Exception as e:
            print(f"✕ Error creating tables: {e}")

if __name__ == '__main__':
    init_postgres_db()