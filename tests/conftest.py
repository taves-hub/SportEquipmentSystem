import pytest
from app import create_app
from extensions import db
from models import Admin, Equipment
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        # seed minimal data
        admin = Admin(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        eq = Equipment(name='Football', category='Ball', category_code='FB001', quantity=5, serial_number='SN001')
        db.session.add(eq)
        db.session.commit()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username='admin', password='admin123'):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)
