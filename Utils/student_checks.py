from models import IssuedEquipment
from extensions import db

def has_unreturned_items(student_id):
    """
    Check if a student has any unreturned equipment.
    Returns:
        tuple: (bool, list) - (has_unreturned, list_of_unreturned_items)
    """
    unreturned = IssuedEquipment.query.filter_by(
        student_id=student_id,
        status='Issued'
    ).all()
    
    return bool(unreturned), unreturned