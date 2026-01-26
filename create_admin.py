from app import create_app
from extensions import db
from models import Admin
from werkzeug.security import generate_password_hash

def create_admin():
    app = create_app()
    with app.app_context():
        # Check if admin already exists
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user created successfully!")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("! Admin user already exists")

if __name__ == '__main__':
    create_admin()