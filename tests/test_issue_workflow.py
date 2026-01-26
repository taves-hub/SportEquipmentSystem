import pytest
import json
from app import create_app
from extensions import db
from models import Admin, Equipment, IssuedEquipment
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    # Create app with in-memory sqlite for testing
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        # create admin
        admin = Admin(username='admin', email='admin@example.com', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        # create equipment item
        eq = Equipment(name='Football', category='Ball', category_code='BALL', quantity=5, serial_number='SN001')
        db.session.add(eq)
        db.session.commit()
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def login(client, username='admin', password='admin123'):
    return client.post('/login', data={'username': username, 'password': password}, follow_redirects=True)

def test_valid_issue_reduces_quantity(app, client):
    # login first
    rv = login(client)
    assert b'Dashboard' in rv.data or rv.status_code == 200

    # get equipment id
    with app.app_context():
        eq = Equipment.query.filter_by(name='Football').first()
        assert eq is not None
        eq_id = eq.id

    # issue 3 items
    rv = client.post('/admin/issue', data={
        'person_type': 'student',
        'student_id': 'S100', 
        'student_name': 'Alice',
        'student_email': 'alice@example.com',
        'student_phone': '0712345678',
        'equipment_id': str(eq_id),
        'quantity': '3',
        'expected_return': '2026-12-01'
    }, follow_redirects=True)
    assert b'Equipment issued successfully' in rv.data

    with app.app_context():
        eq = db.session.get(Equipment, eq_id)
        assert eq.quantity == 2
        issued = IssuedEquipment.query.filter_by(student_id='S100').first()
        assert issued is not None
        assert issued.quantity == 3
        assert issued.expected_return is not None

def test_over_issue_is_blocked(app, client):
    login(client)
    with app.app_context():
        eq = Equipment.query.filter_by(name='Football').first()
        eq_id = eq.id

    # attempt to over-issue (more than available: available currently 2 from previous test or 5 if tests isolated)
    rv = client.post('/admin/issue', data={
        'person_type': 'student',
        'student_id': 'S200', 
        'student_name': 'Bob',
        'student_email': 'bob@example.com',
        'student_phone': '0712345678',
        'equipment_id': str(eq_id), 
        'quantity': '100',
        'expected_return': '2026-12-01'
    }, follow_redirects=True)
    assert b'Not enough items available' in rv.data or b'Not enough items available' in rv.data

def test_return_good_restores_quantity(app, client):
    """Test that returning an item as 'Good' restores it to available inventory"""
    login(client)
    
    with app.app_context():
        eq = Equipment.query.filter_by(name='Football').first()
        initial_quantity = eq.quantity
        
        # Issue 2 items
        rv = client.post('/admin/issue', data={
            'person_type': 'student',
            'student_id': 'S300',
            'student_name': 'Carol',
            'student_email': 'carol@example.com',
            'student_phone': '0712345678',
            'equipment_id': str(eq.id),
            'quantity': '2',
            'expected_return': '2026-12-01'
        }, follow_redirects=True)
        assert b'Equipment issued successfully' in rv.data
        
        # Get the issue record
        issue = IssuedEquipment.query.filter_by(student_id='S300').first()
        assert issue is not None
        
        # Return as Good
        rv = client.post(f'/admin/return/{issue.id}', data={
            'condition': 'Good'
        }, follow_redirects=True)
        assert b'returned successfully' in rv.data
        
        # Verify quantity restored
        eq = db.session.get(Equipment, eq.id)
        assert eq.quantity == initial_quantity  # Should be back to original
        
        # Verify issue record updated
        issue = db.session.get(IssuedEquipment, issue.id)
        assert issue.status == 'Returned'
        assert json.loads(issue.return_conditions)['all'] == 'Good'
        assert issue.date_returned is not None

def test_return_damaged_updates_counter(app, client):
    """Test that returning an item as 'Damaged' increases damaged_count but not quantity"""
    login(client)
    
    with app.app_context():
        eq = Equipment.query.filter_by(name='Football').first()
        initial_quantity = eq.quantity
        initial_damaged = eq.damaged_count or 0
        
        # Issue 1 item
        rv = client.post('/admin/issue', data={
            'person_type': 'student',
            'student_id': 'S400',
            'student_name': 'Dave',
            'student_email': 'dave@example.com',
            'student_phone': '0712345678',
            'equipment_id': str(eq.id),
            'quantity': '1',
            'expected_return': '2026-12-01'
        }, follow_redirects=True)
        assert b'Equipment issued successfully' in rv.data
        
        # Get the issue record
        issue = IssuedEquipment.query.filter_by(student_id='S400').first()
        assert issue is not None
        
        # Return as Damaged
        rv = client.post(f'/admin/return/{issue.id}', data={
            'condition': 'Damaged'
        }, follow_redirects=True)
        assert b'returned successfully' in rv.data
        
        # Verify counters
        eq = db.session.get(Equipment, eq.id)
        assert eq.quantity == initial_quantity - 1  # Should not be restored
        assert eq.damaged_count == initial_damaged + 1  # Should be incremented
        
        # Verify issue record updated
        issue = db.session.get(IssuedEquipment, issue.id)
        assert issue.status == 'Returned'
        assert json.loads(issue.return_conditions)['all'] == 'Damaged'
        assert issue.date_returned is not None

def test_return_lost_updates_counter(app, client):
    """Test that returning an item as 'Lost' increases lost_count but not quantity"""
    login(client)
    
    with app.app_context():
        eq = Equipment.query.filter_by(name='Football').first()
        initial_quantity = eq.quantity
        initial_lost = eq.lost_count or 0
        
        # Issue 1 item
        rv = client.post('/admin/issue', data={
            'person_type': 'student',
            'student_id': 'S500',
            'student_name': 'Eve',
            'student_email': 'eve@example.com',
            'student_phone': '0712345678',
            'equipment_id': str(eq.id),
            'quantity': '1',
            'expected_return': '2026-12-01'
        }, follow_redirects=True)
        assert b'Equipment issued successfully' in rv.data
        
        # Get the issue record
        issue = IssuedEquipment.query.filter_by(student_id='S500').first()
        assert issue is not None
        
        # Return as Lost
        rv = client.post(f'/admin/return/{issue.id}', data={
            'condition': 'Lost'
        }, follow_redirects=True)
        assert b'returned successfully' in rv.data
        
        # Verify counters
        eq = db.session.get(Equipment, eq.id)
        assert eq.quantity == initial_quantity - 1  # Should not be restored
        assert eq.lost_count == initial_lost + 1  # Should be incremented
        
        # Verify issue record updated
        issue = db.session.get(IssuedEquipment, issue.id)
        assert issue.status == 'Returned'
        assert json.loads(issue.return_conditions)['all'] == 'Lost'
        assert issue.date_returned is not None
    