from models import Clearance, IssuedEquipment
from app import db
from datetime import datetime, UTC

def update_clearance_status(student_id):
    """Automatically updates clearance status based on return status of all issued items."""
    clearance = Clearance.query.filter_by(student_id=student_id).first()
    if not clearance:
        clearance = Clearance(student_id=student_id)
        db.session.add(clearance)

    # Check if all issued equipment for this student has been returned
    issued_items = IssuedEquipment.query.filter_by(student_id=student_id).all()
    
    if not issued_items:
        # No issued items, consider cleared
        clearance.status = 'Cleared'
    else:
        # Check if all items are returned
        all_returned = all(item.status == 'Returned' for item in issued_items)
        if all_returned:
            clearance.status = 'Cleared'
        else:
            clearance.status = 'Pending Clearance'
    
    clearance.last_updated = datetime.now(UTC)
    db.session.commit()
