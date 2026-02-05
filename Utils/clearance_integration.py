from models import IssuedEquipment
from app import db
from datetime import datetime, UTC
import json

def get_clearance_status(recipient_id, recipient_type='student'):
    """
    Calculate clearance status dynamically based on comprehensive criteria.

    Clearance Criteria:
    ===================

    CLEARED:
    - No equipment ever issued to recipient, OR
    - All issued equipment has been returned, AND
    - All returned equipment is in 'Good' condition, OR
    - Any damaged/lost equipment has been marked as 'replaced'

    PENDING:
    - Some equipment is still issued (not returned), OR
    - Some returned equipment is damaged/lost but not yet replaced

    OVERDUE:
    - Equipment is still issued AND past expected return date

    Returns: 'Cleared', 'Pending', or 'Overdue'
    """
    if recipient_type == 'student':
        items = IssuedEquipment.query.filter_by(student_id=recipient_id).all()
    else:
        items = IssuedEquipment.query.filter_by(staff_payroll=recipient_id).all()

    if not items:
        return 'Cleared'  # No items issued = cleared

    # Check for overdue items (past expected return date and still issued)
    today = datetime.now(UTC).date()
    overdue_items = [item for item in items
                    if item.status == 'Issued' and
                    item.expected_return and
                    item.expected_return.date() < today]

    if overdue_items:
        return 'Overdue'

    # Check if all items are returned
    all_returned = all(item.status == 'Returned' for item in items)
    if not all_returned:
        return 'Pending'  # Some items still issued

    # All items are returned - now check return conditions
    # If any item has damaged/lost conditions that haven't been handled (replaced/repaired/waiver), clearance is pending
    for item in items:
        if item.return_conditions:
            try:
                conditions = json.loads(item.return_conditions)
                
                # Check if action has been taken (replaced, repaired, or waiver)
                if isinstance(conditions, dict):
                    # New format with action field
                    if conditions.get('action') in ('replaced', 'repaired', 'waiver'):
                        continue  # This item has been handled, so it's okay
                    
                    # Check for old 'replaced' flag for backwards compatibility
                    if conditions.get('replaced'):
                        continue
                    
                    # Check individual condition values for damaged/lost
                    for condition in conditions.values():
                        if isinstance(condition, str) and condition.lower() in ('damaged', 'lost'):
                            return 'Pending'  # Damaged/lost item not yet handled
                elif isinstance(conditions, str) and conditions.lower() in ('damaged', 'lost'):
                    return 'Pending'  # Damaged/lost item not handled
            except (json.JSONDecodeError, TypeError):
                # If we can't parse conditions, check if it contains damaged/lost keywords
                conditions_str = str(item.return_conditions).lower()
                if 'damaged' in conditions_str or 'lost' in conditions_str:
                    # Check if it also contains our action keywords
                    if 'replaced' not in conditions_str and 'repaired' not in conditions_str and 'waiver' not in conditions_str:
                        return 'Pending'

    # All items returned and all conditions are good or handled
    return 'Cleared'
