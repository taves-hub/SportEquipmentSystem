from app import create_app
from extensions import db
from models import Admin
from werkzeug.security import generate_password_hash
import pymysql

def verify_database_and_create_admin():
    app = create_app()
    
    try:
        # First verify database connection
        print("Step 1: Verifying database connection...")
        with app.app_context():
            connection = pymysql.connect(
                host='localhost',
                user='root',
                password='',
                database='sports_equipment_db'
            )
            print("✓ Database connection successful")
            connection.close()
        
        # Now create tables if they don't exist
        print("\nStep 2: Ensuring database tables exist...")
        with app.app_context():
            db.create_all()
            print("✓ Database tables created/verified")
        
        # Create admin user
        print("\nStep 3: Creating admin user...")
        with app.app_context():
            # Check if admin exists
            admin = Admin.query.filter_by(username='admin').first()
            if admin:
                print("! Admin user already exists, updating password...")
                admin.password_hash = generate_password_hash('admin123')
            else:
                print("! Creating new admin user...")
                admin = Admin(
                    username='admin',
                    email='admin@example.com',
                    password_hash=generate_password_hash('admin123')
                )
                db.session.add(admin)
            
            db.session.commit()
            
            # Verify admin was created
            admin = Admin.query.filter_by(username='admin').first()
            if admin:
                print("✓ Admin user verified in database")
                print("  Username: admin")
                print("  Password: admin123")
                print("  Email:", admin.email)
            else:
                print("✕ Failed to create admin user!")
                
    except Exception as e:
        print("✕ Error:", str(e))
        
    print("\nStep 4: Verifying admin in database...")
    with app.app_context():
        # Double check admin exists
        admin = Admin.query.all()
        print("All users in database:")
        for user in admin:
            print(f"  - {user.username} ({user.email})")

if __name__ == '__main__':
    verify_database_and_create_admin()