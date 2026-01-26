from app import create_app
from extensions import db
from models import StoreKeeper
from werkzeug.security import generate_password_hash


def create_storekeeper(username='storekeeper', email='storekeeper@example.com', password='storekeeper123'):
    app = create_app()
    with app.app_context():
        if not StoreKeeper.query.filter_by(username=username).first():
            sk = StoreKeeper(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(sk)
            db.session.commit()
            print("✓ Storekeeper user created successfully!")
            print("Username:", username)
            print("Password:", password)
        else:
            print("! Storekeeper user already exists")

if __name__ == '__main__':
    create_storekeeper()
