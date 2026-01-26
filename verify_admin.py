from app import create_app
from extensions import db
from models import Admin
from werkzeug.security import generate_password_hash, check_password_hash

def verify_admin():
    app = create_app()
    with app.app_context():
        # Check if admin exists
        admin = Admin.query.filter_by(username='admin').first()
        if admin:
            print("✓ Admin user exists")
            print(f"Username: {admin.username}")
            print(f"Email: {admin.email}")
            # Create a new password and update it
            new_password = 'admin123'
            admin.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print(f"✓ Password reset to: {new_password}")
        else:
            # Create new admin
            new_admin = Admin(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(new_admin)
            db.session.commit()
            print("✓ Created new admin user")
            print("Username: admin")
            print("Password: admin123")

if __name__ == '__main__':
    verify_admin()