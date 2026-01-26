import pytest
from models import IssuedEquipment
from tests.conftest import login  # Reusing login helper from shared fixtures

def test_issue_blocked_with_unreturned_items(app, client):
    """Test that students cannot borrow new items if they have unreturned equipment"""
    login(client)

    with app.app_context():
        # First issue - should succeed
        rv = client.post('/admin/issue', data={
            'person_type': 'student',
            'student_id': 'S600',
            'student_name': 'Frank',
            'student_email': 'frank@example.com',
            'student_phone': '0712345678',
            'equipment_id': '1',
            'quantity': '1',
            'expected_return': '2026-12-01'
        }, follow_redirects=True)
        assert b'Equipment issued successfully' in rv.data

        # create a second equipment to attempt issuing
        from extensions import db
        from models import Equipment
        eq2 = Equipment(name='Basketball', category='Ball', category_code='BALL2', quantity=3, serial_number='SN002')
        db.session.add(eq2)
        db.session.commit()

        # Second issue attempt - should be blocked (student still has unreturned item)
        rv = client.post('/admin/issue', data={
            'person_type': 'student',
            'student_id': 'S600',
            'student_name': 'Frank',
            'student_email': 'frank@example.com',
            'student_phone': '0712345678',
            'equipment_id': str(eq2.id),
            'quantity': '1',
            'expected_return': '2026-12-01'
        }, follow_redirects=True)
        assert b'Student has unreturned items' in rv.data

        # Return the first item
        issue = IssuedEquipment.query.filter_by(student_id='S600').first()
        rv = client.post(f'/admin/return/{issue.id}', data={
            'condition': 'Good'
        }, follow_redirects=True)
        assert b'returned successfully' in rv.data

        # Third issue attempt after return - should succeed
        rv = client.post('/admin/issue', data={
            'person_type': 'student',
            'student_id': 'S600',
            'student_name': 'Frank',
            'student_email': 'frank@example.com',
            'student_phone': '0712345678',
            'equipment_id': str(eq2.id),
            'quantity': '1',
            'expected_return': '2026-12-01'
        }, follow_redirects=True)
        assert b'Equipment issued successfully' in rv.data