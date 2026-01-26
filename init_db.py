from app import create_app, db

def init_database():
    try:
        app = create_app()
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✓ Successfully created all database tables:")
            print("  - admins")
            print("  - equipment")
            print("  - issued_equipment")
            print("  - clearance")
            
    except Exception as e:
        print("❌ Failed to create database tables!")
        print(f"Error: {e}")

if __name__ == "__main__":
    init_database()