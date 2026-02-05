from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, abort
from flask_login import login_required, current_user
from models import StoreKeeper, Equipment, IssuedEquipment, CampusDistribution, Student, Staff
from extensions import db
from datetime import datetime, UTC
from sqlalchemy import func
from Utils.student_checks import has_unreturned_items
import json

storekeeper_bp = Blueprint('storekeeper', __name__, url_prefix='/storekeeper')


from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, abort
from flask_login import login_required, current_user
from models import StoreKeeper, Equipment, IssuedEquipment, CampusDistribution, Student, Staff
from extensions import db
from datetime import datetime, UTC
from sqlalchemy import func
from Utils.student_checks import has_unreturned_items
import json

storekeeper_bp = Blueprint('storekeeper', __name__, url_prefix='/storekeeper')

@storekeeper_bp.route('/clearance-report', methods=['GET'])
@login_required
def clearance_report():
    """Show clearance status for students/staff issued by this storekeeper only."""
    # Only allow storekeepers
    if not (current_user.is_authenticated and isinstance(current_user, StoreKeeper)):
        abort(403)
    recipient_id = request.args.get('student_id', '').strip()
    query = IssuedEquipment.query.filter_by(issued_by=current_user.payroll_number)
    if recipient_id:
        query = query.filter(
            db.or_(
                IssuedEquipment.student_id.ilike(f"%{recipient_id}%"),
                IssuedEquipment.staff_payroll.ilike(f"%{recipient_id}%")
            )
        )
    issued_items = query.order_by(IssuedEquipment.date_issued.desc()).all()
    clearance_counts = {'Cleared': 0, 'Pending': 0, 'Overdue': 0, 'Total': 0}
    status_map = {}
    recipient_info = {}
    recipient_ids = set()
    for it in issued_items:
        if it.student_id:
            recipient_ids.add(('student', it.student_id))
        elif it.staff_payroll:
            recipient_ids.add(('staff', it.staff_payroll))
    clearance_counts['Total'] = len(recipient_ids)
    from Utils.clearance_integration import get_clearance_status
    for recipient_type, rid in recipient_ids:
        status = get_clearance_status(rid, recipient_type)
        status_map[rid] = status
        clearance_counts[status] = clearance_counts.get(status, 0) + 1
        recipient_name = 'Unknown'
        issued_by_display = current_user.full_name or current_user.payroll_number
        campus_name = current_user.campus.name if hasattr(current_user, 'campus') and current_user.campus else ''
        if recipient_type == 'student':
            student = Student.query.get(rid)
            if student:
                recipient_name = student.name
        else:
            staff = Staff.query.get(rid)
            if staff:
                recipient_name = staff.name
        recipient_info[rid] = {
            'name': recipient_name,
            'type': 'Student' if recipient_type == 'student' else 'Staff',
            'issued_by': issued_by_display,
            'campus': campus_name
        }
    return render_template('clearance_report.html',
                           issued_items=issued_items,
                           student_id=recipient_id,
                           is_pdf=False,
                           clearance_status_map=status_map,
                           clearance_counts=clearance_counts,
                           recipient_info=recipient_info,
                           is_student=any(it.student for it in issued_items),
                           is_staff=any(it.staff for it in issued_items))

# Receipts page: search and list all receipts for a student or staff
@storekeeper_bp.route('/receipts', methods=['GET'])
@login_required
def receipts():
    recipient_id = request.args.get('recipient_id', '').strip()
    recipient = None
    issues = []
    if recipient_id:
        # Try student first
        recipient = Student.query.filter_by(id=recipient_id).first()
        if recipient:
            issues = IssuedEquipment.query.filter_by(student_id=recipient_id).order_by(IssuedEquipment.date_issued.desc()).all()
        else:
            recipient = Staff.query.filter_by(payroll_number=recipient_id).first()
            if recipient:
                issues = IssuedEquipment.query.filter_by(staff_payroll=recipient_id).order_by(IssuedEquipment.date_issued.desc()).all()
    return render_template('storekeeper_receipts.html', recipient=recipient, recipient_id=recipient_id, issues=issues)


def aggregate_distributions(campus_id):
    """
    Aggregate multiple distributions of the same equipment to the same campus.
    Groups by equipment_id and sums quantities.
    Returns a dict: {equipment_id: {'quantity': total_qty, 'equipment': Equipment, 'category_code': code, 'category_name': name}}
    """
    distributions = CampusDistribution.query.filter_by(campus_id=campus_id).all()
    aggregated = {}
    
    for dist in distributions:
        eq_id = dist.equipment_id
        if eq_id not in aggregated:
            aggregated[eq_id] = {
                'quantity': 0,
                'equipment': dist.equipment,
                'category_code': dist.category_code,
                'category_name': dist.category_name
            }
        aggregated[eq_id]['quantity'] += dist.quantity
    
    return aggregated

@storekeeper_bp.before_request
def _require_storekeeper():
    # ensure current user is a storekeeper; otherwise redirect
    if not current_user.is_authenticated:
        return
    if not isinstance(current_user, StoreKeeper):
        # if an admin is logged in, send them to admin dashboard
        return redirect(url_for('admin.dashboard'))

@storekeeper_bp.route('/dashboard')
@login_required
def dashboard():
    # Get aggregated equipment distributed to this storekeeper's campus
    aggregated = aggregate_distributions(current_user.campus_id)
    
    # Build a dict of equipment_id -> distributed_quantity
    distributed_qty = {eq_id: data['quantity'] for eq_id, data in aggregated.items()}
    equipment_ids = list(distributed_qty.keys())
    
    if equipment_ids:
        campus_equipment = Equipment.query.filter(Equipment.id.in_(equipment_ids)).all()
        total_equipment = len(campus_equipment)
        total_active = sum(1 for eq in campus_equipment if eq.is_active)
        
        # Calculate low stock based on distributed quantities minus issued
        low_stock = []
        for eq in campus_equipment:
            issued_count = IssuedEquipment.query.filter_by(
                equipment_id=eq.id,
                issued_by=current_user.payroll_number,
                status='Issued'
            ).with_entities(func.sum(IssuedEquipment.quantity)).scalar() or 0
            available = distributed_qty[eq.id] - issued_count
            if available <= 5:
                low_stock.append((eq, available, distributed_qty[eq.id]))
    else:
        total_equipment = 0
        total_active = 0
        low_stock = []
    
    # Get issued items for this storekeeper
    # Build issued query scoped to equipment IDs if any distributed to this campus
    issued_q = IssuedEquipment.query.filter(
        IssuedEquipment.issued_by == current_user.payroll_number,
        IssuedEquipment.status == 'Issued'
    )
    if equipment_ids:
        issued_q = issued_q.filter(IssuedEquipment.equipment_id.in_(equipment_ids))
    total_issued = issued_q.count()
    
    low_stock = sorted(low_stock, key=lambda x: x[1])
    
    today = datetime.now().date()
    due_q = IssuedEquipment.query.filter(
        IssuedEquipment.issued_by == current_user.payroll_number,
        IssuedEquipment.status == 'Issued',
        IssuedEquipment.expected_return != None,
        func.date(IssuedEquipment.expected_return) <= today
    )
    if equipment_ids:
        due_q = due_q.filter(IssuedEquipment.equipment_id.in_(equipment_ids))
    due_items = due_q.order_by(IssuedEquipment.expected_return.asc()).all()
    
    return render_template('storekeeper_dashboard.html',
                           total_equipment=total_equipment,
                           total_active=total_active,
                           total_issued=total_issued,
                           low_stock=low_stock,
                           due_items=due_items,
                           current_user=current_user,
                           campus_name=current_user.campus.name if current_user.campus else 'Unknown')


@storekeeper_bp.route('/equipment')
@login_required
def equipment():
    # Get aggregated equipment distributed to this storekeeper's campus only
    aggregated = aggregate_distributions(current_user.campus_id)
    
    # Build equipment list with available quantities
    equipment_list = []
    for eq_id, dist_data in aggregated.items():
        eq = dist_data['equipment']
        if eq:
            # Calculate how much has been issued by this storekeeper
            issued_count = IssuedEquipment.query.filter_by(
                equipment_id=eq.id,
                issued_by=current_user.payroll_number,
                status='Issued'
            ).with_entities(func.sum(IssuedEquipment.quantity)).scalar() or 0
            
            available = dist_data['quantity'] - issued_count
            equipment_list.append({
                'equipment': eq,
                'distributed_quantity': dist_data['quantity'],
                'issued_quantity': issued_count,
                'available_quantity': available
            })
    
    # Sort by category and name
    equipment_list = sorted(equipment_list, key=lambda x: (x['equipment'].category, x['equipment'].name))
    
    return render_template('storekeeper_equipment.html', equipment=equipment_list)


@storekeeper_bp.route('/issued-equipment')
@login_required
def issued_equipment():
    # Group issued equipment by recipient to eliminate redundancy
    from collections import defaultdict
    from datetime import datetime

    # Get all issued equipment created by this storekeeper
    issuer_identifier = getattr(current_user, 'payroll_number', None)
    if issuer_identifier:
        all_issued = IssuedEquipment.query.filter_by(issued_by=issuer_identifier).order_by(IssuedEquipment.date_issued.desc()).all()
    else:
        all_issued = []

    # Group by recipient
    recipient_groups = defaultdict(list)
    for issue in all_issued:
        recipient_key = issue.student_id or issue.staff_payroll
        if recipient_key:
            recipient_groups[recipient_key].append(issue)

    # Create aggregated records
    aggregated_issued = []
    for recipient_key, issues in recipient_groups.items():
        # Find the most recent issue for this recipient
        most_recent = max(issues, key=lambda x: x.date_issued or datetime.min)

        # Calculate totals
        total_quantity = sum(issue.quantity for issue in issues)
        has_outstanding = any(issue.status == 'Issued' for issue in issues)

        # Collect all equipment names
        equipment_names = []
        seen_equipment = set()
        for issue in issues:
            eq_name = issue.equipment.name if issue.equipment else str(issue.equipment_id)
            if eq_name not in seen_equipment:
                equipment_names.append(eq_name)
                seen_equipment.add(eq_name)

        equipment_display = ', '.join(equipment_names) if len(equipment_names) <= 3 else f"{', '.join(equipment_names[:3])}, +{len(equipment_names)-3} more"

        # Create a representative issue object with aggregated data
        class AggregatedIssue:
            def __init__(self, representative_issue, total_quantity, equipment_display, has_outstanding):
                self.student = representative_issue.student
                self.staff = representative_issue.staff
                self.student_id = representative_issue.student_id
                self.staff_payroll = representative_issue.staff_payroll
                self.equipment = representative_issue.equipment  # Keep first equipment for compatibility
                self.equipment_display = equipment_display
                self.quantity = total_quantity
                self.date_issued = most_recent.date_issued
                self.issued_by = most_recent.issued_by
                self.expected_return = most_recent.expected_return
                self.status = 'Issued' if has_outstanding else 'Returned'
                self.id = representative_issue.id  # Keep an ID for return functionality

        aggregated_issue = AggregatedIssue(most_recent, total_quantity, equipment_display, has_outstanding)
        aggregated_issued.append(aggregated_issue)

    # Sort by most recent issue date
    aggregated_issued.sort(key=lambda x: x.date_issued or datetime.min, reverse=True)

    return render_template('issued_equipment.html', issued=aggregated_issued)


@storekeeper_bp.route('/api/recipient-autocomplete')
@login_required
def recipient_autocomplete():
    """API endpoint for recipient autocomplete suggestions"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    # Search for students and staff with issued equipment
    results = []

    # Search students
    students = db.session.query(
        IssuedEquipment.student_id.label('id'),
        IssuedEquipment.student_name.label('name'),
        db.literal('Student').label('type')
    ).filter(
        IssuedEquipment.student_id.isnot(None),
        IssuedEquipment.student_id.ilike(f'%{query}%'),
        IssuedEquipment.status == 'Issued'
    ).distinct().limit(10).all()

    for student in students:
        results.append({
            'id': student.id,
            'name': student.name,
            'type': student.type,
            'display': f"{student.name} ({student.id}) - Student"
        })

    # Search staff
    staff = db.session.query(
        IssuedEquipment.staff_payroll.label('id'),
        Staff.name.label('name'),
        db.literal('Staff').label('type')
    ).join(Staff, IssuedEquipment.staff_payroll == Staff.payroll_number).filter(
        IssuedEquipment.staff_payroll.isnot(None),
        IssuedEquipment.staff_payroll.ilike(f'%{query}%'),
        IssuedEquipment.status == 'Issued'
    ).distinct().limit(10).all()

    for person in staff:
        results.append({
            'id': person.id,
            'name': person.name,
            'type': person.type,
            'display': f"{person.name} ({person.id}) - Staff"
        })

    return jsonify(results)


@storekeeper_bp.route('/return-equipment', methods=['GET', 'POST'])
@login_required
def return_equipment():
    """Return Equipment module: select student/staff and display all their issued equipment"""
    recipient_id = request.args.get('recipient_id', '').strip()
    issue_id = request.args.get('issue_id', '').strip()
    
    if request.method == 'POST':
        # Handle return of selected items
        selected_serials = request.form.getlist('selected_serials')
        if not selected_serials:
            flash('No items selected for return.', 'warning')
            return redirect(url_for('storekeeper.return_equipment', recipient_id=recipient_id))
        
        # Group serials by issue for processing
        serials_by_issue = {}
        for selected_serial in selected_serials:
            if ':' in selected_serial:
                issue_id, serial = selected_serial.split(':', 1)
                if issue_id not in serials_by_issue:
                    serials_by_issue[issue_id] = []
                serials_by_issue[issue_id].append(serial)
            else:
                # Handle non-serial items (shouldn't happen with new form, but for compatibility)
                issue_id = selected_serial
                if issue_id not in serials_by_issue:
                    serials_by_issue[issue_id] = []
        
        # Process returns for all selected items
        successful_returns = 0
        failed_returns = 0
        error_messages = []
        
        for issue_id, selected_serials_in_issue in serials_by_issue.items():
            try:
                issue = IssuedEquipment.query.get_or_404(issue_id)
                
                # Skip if already returned
                if issue.status == 'Returned':
                    error_messages.append(f'Item {issue_id} has already been returned.')
                    failed_returns += 1
                    continue
                
                # Parse all serial numbers for this issue
                all_serials = []
                if issue.serial_numbers:
                    try:
                        all_serials = json.loads(issue.serial_numbers)
                    except:
                        all_serials = []
                
                # Get conditions for each selected serial
                conditions = {}
                for serial in selected_serials_in_issue:
                    condition_key = f'condition_{issue_id}_{serial}'
                    condition = request.form.get(condition_key)
                    if not condition or condition not in ('Good', 'Damaged', 'Lost'):
                        error_messages.append(f'Invalid condition for serial {serial} in item {issue_id}.')
                        failed_returns += 1
                        continue
                    conditions[serial] = condition
                
                if not conditions:
                    continue
                
                # Check if all serials are being returned
                all_selected = len(selected_serials_in_issue) == len(all_serials) if all_serials else True
                
                if all_selected:
                    # All serials are being returned - mark issue as returned
                    issue.status = 'Returned'
                    issue.return_conditions = json.dumps(conditions)
                    issue.date_returned = datetime.now(UTC)
                else:
                    # Partial return - update return_conditions but keep issue as Issued
                    existing_conditions = {}
                    if issue.return_conditions:
                        try:
                            existing_conditions = json.loads(issue.return_conditions)
                        except:
                            pass
                    
                    # Merge new conditions with existing ones
                    existing_conditions.update(conditions)
                    issue.return_conditions = json.dumps(existing_conditions)
                    
                    # Only mark as returned if all serials have been returned
                    if len(existing_conditions) >= len(all_serials):
                        issue.status = 'Returned'
                        issue.date_returned = datetime.now(UTC)
                
                # Update equipment counts based on conditions
                equipment = Equipment.query.get_or_404(issue.equipment_id)
                good_count = sum(1 for c in conditions.values() if c == 'Good')
                damaged_count = sum(1 for c in conditions.values() if c == 'Damaged')
                lost_count = sum(1 for c in conditions.values() if c == 'Lost')
                
                equipment.quantity += good_count
                equipment.damaged_count += damaged_count
                equipment.lost_count += lost_count
                
                successful_returns += 1
                
            except Exception as e:
                error_messages.append(f'Error processing item {issue_id}: {str(e)}')
                failed_returns += 1
        
        # Commit all changes
        try:
            db.session.commit()
            
            # Update clearance status if any student items were returned
            student_ids = set()
            for issue_id in serials_by_issue.keys():
                issue = IssuedEquipment.query.get(issue_id)
                if issue and issue.student_id:
                    student_ids.add(issue.student_id)
            
            for student_id in student_ids:
                try:
                    pass  # Clearance status is now calculated dynamically
                except Exception:
                    pass
            
            # Flash results
            if successful_returns > 0:
                flash(f'Successfully returned {successful_returns} item(s).', 'success')
            if failed_returns > 0:
                flash(f'Failed to return {failed_returns} item(s).', 'danger')
                if error_messages:
                    for msg in error_messages:
                        flash(msg, 'warning')
                        
        except Exception as e:
            db.session.rollback()
            flash(f'Error committing changes: {str(e)}', 'danger')
        
        return redirect(url_for('storekeeper.return_equipment', recipient_id=recipient_id))
    
    # GET: Show search form and issued equipment for selected recipient
    issued_items = []
    recipient_name = ""
    recipient_type = ""
    display_items = []
    
    if issue_id:
        # Try numeric issue id first
        issue = None
        try:
            issue_pk = int(issue_id)
            issue = IssuedEquipment.query.get(issue_pk)
        except Exception:
            issue = None

        if issue:
            # Ensure the current storekeeper created the issue and it belongs to this campus
            aggregated = aggregate_distributions(current_user.campus_id)
            campus_equipment_ids = list(aggregated.keys())
            if issue.issued_by != getattr(current_user, 'payroll_number', None) or issue.equipment_id not in campus_equipment_ids:
                issue = None

        if issue:
            issued_items = [issue]
        else:
            # If the provided value isn't a numeric issue id, fall back to treating it as a recipient id
            recipient_id = issue_id
            # proceed to recipient search below
            issued_items = []
    if recipient_id:
        # Find issued equipment for this recipient
        # Get aggregated equipment distributed to this storekeeper's campus only
        aggregated = aggregate_distributions(current_user.campus_id)
        campus_equipment_ids = list(aggregated.keys())
        
        # Find issued equipment for this recipient from campus
        issued_q = IssuedEquipment.query.filter(
            db.or_(
                IssuedEquipment.student_id.ilike(f"%{recipient_id}%"),
                IssuedEquipment.staff_payroll.ilike(f"%{recipient_id}%")
            ),
            IssuedEquipment.status == 'Issued'
        )
        if campus_equipment_ids:
            issued_q = issued_q.filter(IssuedEquipment.equipment_id.in_(campus_equipment_ids))
        issued_items = issued_q.order_by(IssuedEquipment.date_issued.desc()).all()
        
        # Determine recipient type and name
        if issued_items:
            first_item = issued_items[0]
            if first_item.student:
                recipient_type = "Student"
                recipient_name = first_item.student.name
            elif first_item.staff:
                recipient_type = "Staff/Trainer"
                recipient_name = first_item.staff.name
        
        # Create display items with parsed serials
        for item in issued_items:
            if item.serial_numbers:
                try:
                    serials = json.loads(item.serial_numbers)
                except:
                    serials = []
            else:
                serials = []
            
            if serials:
                # For items with serials, create one entry per serial
                for serial in serials:
                    display_items.append({
                        'issue': item,
                        'serial': serial,
                        'equipment_name': item.equipment.name if item.equipment else item.equipment_id
                    })
            else:
                # For items without serials, create one entry
                display_items.append({
                    'issue': item,
                    'serial': None,
                    'equipment_name': item.equipment.name if item.equipment else item.equipment_id
                })
    
    return render_template('return_equipment.html', 
                         display_items=display_items,
                         recipient_id=recipient_id,
                         recipient_name=recipient_name,
                         recipient_type=recipient_type)


@storekeeper_bp.route('/return/<int:issue_id>', methods=['GET', 'POST'])
@login_required
def return_item(issue_id):
    issue = IssuedEquipment.query.get_or_404(issue_id)
    if issue.status == 'Returned':
        flash('This item has already been returned.', 'warning')
        return redirect(url_for('storekeeper.issued_equipment'))

    # Parse serial numbers
    serials = []
    if issue.serial_numbers:
        try:
            serials = json.loads(issue.serial_numbers)
        except:
            serials = []

    if request.method == 'GET':
        return render_template('return_form.html', issue=issue, serials=serials)

    condition = request.form.get('condition')
    returned_serials = request.form.getlist('returned_serials')
    
    # Validate serial numbers if present
    if serials:
        if set(returned_serials) != set(serials):
            flash('Please check all serial numbers of the items being returned.', 'danger')
            return redirect(url_for('storekeeper.return_item', issue_id=issue_id))
        
        # Collect conditions per serial
        conditions = {}
        for serial in returned_serials:
            condition = request.form.get(f'condition_{serial}')
            if not condition or condition not in ('Good', 'Damaged', 'Lost'):
                flash(f'Please select a valid return condition for serial number {serial}.', 'danger')
                return redirect(url_for('storekeeper.return_item', issue_id=issue_id))
            conditions[serial] = condition
    else:
        # For non-serial items, use single condition
        condition = request.form.get('condition')
        if not condition or condition not in ('Good', 'Damaged', 'Lost'):
            flash('Please select a valid return condition.', 'danger')
            return redirect(url_for('storekeeper.return_item', issue_id=issue_id))
        conditions = condition

    equipment = Equipment.query.get_or_404(issue.equipment_id)
    issue.status = 'Returned'
    if serials:
        issue.return_conditions = json.dumps(conditions)
    else:
        issue.return_conditions = json.dumps({'all': condition})
    issue.date_returned = datetime.now(UTC)

    # Update equipment counts based on conditions
    if serials:
        good_count = sum(1 for c in conditions.values() if c == 'Good')
        damaged_count = sum(1 for c in conditions.values() if c == 'Damaged')
        lost_count = sum(1 for c in conditions.values() if c == 'Lost')
    else:
        if condition == 'Good':
            good_count = issue.quantity
            damaged_count = 0
            lost_count = 0
        elif condition == 'Damaged':
            good_count = 0
            damaged_count = issue.quantity
            lost_count = 0
        else:
            good_count = 0
            damaged_count = 0
            lost_count = issue.quantity

    equipment.quantity += good_count
    equipment.damaged_count += damaged_count
    equipment.lost_count += lost_count

    try:
        db.session.commit()
        # update clearance only when student_id exists
        try:
            pass  # Clearance status is now calculated dynamically
        except Exception:
            pass
        flash(f'Item returned successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Error processing return. Please try again.', 'danger')
        return redirect(url_for('storekeeper.return_item', issue_id=issue_id))

    return redirect(url_for('storekeeper.issued_equipment'))

@storekeeper_bp.route('/issue', methods=['GET', 'POST'])
@login_required
def issue():
    if request.method == 'GET':
        # Get aggregated equipment distributed to this storekeeper's campus only
        aggregated = aggregate_distributions(current_user.campus_id)
        
        # Build equipment list with available quantities
        equipment = []
        for eq_id, dist_data in aggregated.items():
            eq = dist_data['equipment']
            if eq and eq.is_active:
                # Calculate how much has been issued by this storekeeper
                issued_count = IssuedEquipment.query.filter_by(
                    equipment_id=eq.id,
                    issued_by=current_user.payroll_number,
                    status='Issued'
                ).with_entities(func.sum(IssuedEquipment.quantity)).scalar() or 0
                
                available = dist_data['quantity'] - issued_count
                if available > 0:  # Only show equipment with available quantity
                    equipment.append({
                        'id': eq.id,
                        'name': eq.name,
                        'available': available,
                        'distributed': dist_data['quantity'],
                        'issued': issued_count
                    })
        
        equipment = sorted(equipment, key=lambda x: x['name'])
        issued = IssuedEquipment.query.filter_by(issued_by=current_user.payroll_number).order_by(IssuedEquipment.date_issued.desc()).all()
        return render_template('issue.html', equipment=equipment, issued=issued)

    person_type = request.form.get('person_type')
    student_id = request.form.get('student_id')
    student_name = request.form.get('student_name')
    student_email = request.form.get('student_email')
    student_phone = request.form.get('student_phone')
    staff_payroll = request.form.get('staff_payroll')
    staff_name = request.form.get('staff_name')
    staff_email = request.form.get('staff_email')
    equipment_id = request.form.get('equipment_id')
    qty = int(request.form.get('quantity', 1))
    expected_return_str = request.form.get('expected_return')
    serial_numbers = request.form.getlist('serial_numbers')
    
    # Validate serial number uniqueness across database
    if serial_numbers:
        existing_serials = set()
        for issue in IssuedEquipment.query.filter(IssuedEquipment.serial_numbers.isnot(None)):
            try:
                serials = json.loads(issue.serial_numbers)
                existing_serials.update(serials)
            except:
                pass  # Skip invalid JSON
        for sn in serial_numbers:
            if sn.strip() and sn.strip() in existing_serials:
                flash(f'Serial number "{sn.strip()}" is already in use. Please use a different serial number.', 'danger')
                return redirect(url_for('storekeeper.issue'))

    if person_type == 'student':
        if not student_id or not student_name or not student_email or not student_phone:
            flash('Missing required student fields.', 'danger')
            return redirect(url_for('storekeeper.issue'))
        if '@' not in student_email or '.' not in student_email:
            flash('Invalid student email address.', 'danger')
            return redirect(url_for('storekeeper.issue'))
        import re
        if not re.fullmatch(r'0\d{9}', student_phone or ''):
            flash('Invalid phone number. Expected format: 0712345678', 'danger')
            return redirect(url_for('storekeeper.issue'))
        has_unreturned, unreturned_items = has_unreturned_items(student_id)
        if has_unreturned:
            # Parse serial numbers for each unreturned item
            for item in unreturned_items:
                serials = []
                if item.serial_numbers:
                    try:
                        import json
                        serials = json.loads(item.serial_numbers)
                    except Exception:
                        serials = []
                elif item.equipment and getattr(item.equipment, 'serial_number', None):
                    serials = [item.equipment.serial_number]
                item.serials = serials
            equipment = []
            aggregated = aggregate_distributions(current_user.campus_id)
            for eq_id, dist_data in aggregated.items():
                eq = dist_data['equipment']
                if eq and eq.is_active:
                    issued_count = IssuedEquipment.query.filter_by(
                        equipment_id=eq.id,
                        issued_by=current_user.payroll_number,
                        status='Issued'
                    ).with_entities(func.sum(IssuedEquipment.quantity)).scalar() or 0
                    available = dist_data['quantity'] - issued_count
                    if available > 0:
                        equipment.append({
                            'id': eq.id,
                            'name': eq.name,
                            'available': available,
                            'distributed': dist_data['quantity'],
                            'issued': issued_count
                        })
            equipment = sorted(equipment, key=lambda x: x['name'])
            # Persist all original form data for modal confirmation
            original_form = request.form.to_dict(flat=False)
            return render_template('issue.html',
                equipment=equipment,
                show_unreturned_modal=True,
                unreturned_items=unreturned_items,
                student_name=student_name,
                student_id=student_id,
                original_form=original_form
            )
    elif person_type == 'staff':
        if not staff_payroll or not staff_name or not staff_email:
            flash('Missing required staff fields.', 'danger')
            return redirect(url_for('storekeeper.issue'))
        if '@' not in staff_email or '.' not in staff_email:
            flash('Invalid staff email address.', 'danger')
            return redirect(url_for('storekeeper.issue'))
    else:
        flash('Please select who to issue to.', 'danger')
        return redirect(url_for('storekeeper.issue'))
    if not equipment_id:
        flash('Equipment selection required.', 'danger')
        return redirect(url_for('storekeeper.issue'))
    try:
        eq = db.session.get(Equipment, int(equipment_id))
    except Exception:
        eq = None
    if not eq:
        flash('Selected equipment not found.', 'danger')
        return redirect(url_for('storekeeper.issue'))
    
    # Get aggregated distributions for this campus
    aggregated = aggregate_distributions(current_user.campus_id)
    
    try:
        equipment_id_int = int(equipment_id)
    except Exception:
        flash('Invalid equipment selection.', 'danger')
        return redirect(url_for('storekeeper.issue'))

    if equipment_id_int not in aggregated:
        flash('This equipment is not distributed to your campus.', 'danger')
        return redirect(url_for('storekeeper.issue'))

    dist_data = aggregated[equipment_id_int]
    
    # Calculate how much has been issued already
    issued_count = IssuedEquipment.query.filter_by(
        equipment_id=equipment_id_int,
        issued_by=current_user.payroll_number,
        status='Issued'
    ).with_entities(func.sum(IssuedEquipment.quantity)).scalar() or 0
    
    available = dist_data['quantity'] - issued_count
    if available < qty:
        flash(f'Not enough items available. Distributed: {dist_data["quantity"]}, Already issued: {issued_count}, Available: {available}', 'danger')
        return redirect(url_for('storekeeper.issue'))
    expected_return = None
    if expected_return_str:
        try:
            expected_return = datetime.strptime(expected_return_str, '%Y-%m-%d')
        except ValueError:
            flash('Invalid expected return date format.', 'danger')
            return redirect(url_for('storekeeper.issue'))
        today_date = datetime.now().date()
        if expected_return.date() < today_date:
            flash('Expected return date cannot be in the past. Please select today or a future date.', 'danger')
            return redirect(url_for('storekeeper.issue'))
    # Create or update Student/Staff record as needed, then create IssuedEquipment
    if person_type == 'student':
        student = Student.query.filter_by(id=student_id).first()
        if not student:
            student = Student(
                id=student_id,
                name=student_name,
                email=student_email,
                phone=student_phone
            )
            db.session.add(student)
        else:
            student.name = student_name
            student.email = student_email
            student.phone = student_phone
            db.session.add(student)

        issue = IssuedEquipment(
            student_id=student_id,
            equipment_id=eq.id,
            quantity=qty,
            expected_return=expected_return,
            serial_numbers=json.dumps(serial_numbers) if serial_numbers else None
        )
    else:
        staff = Staff.query.filter_by(payroll_number=staff_payroll).first()
        if not staff:
            staff = Staff(
                payroll_number=staff_payroll,
                name=staff_name,
                email=staff_email
            )
            db.session.add(staff)
        else:
            staff.name = staff_name
            staff.email = staff_email
            db.session.add(staff)

        issue = IssuedEquipment(
            student_id=None,
            staff_payroll=staff_payroll,
            equipment_id=eq.id,
            quantity=qty,
            expected_return=expected_return,
            serial_numbers=json.dumps(serial_numbers) if serial_numbers else None
        )

    # record who issued this item (storekeeper payroll_number)
    try:
        issue.issued_by = getattr(current_user, 'payroll_number', None) or getattr(current_user, 'full_name', None)
    except Exception:
        issue.issued_by = None


    db.session.add(issue)
    eq.quantity = eq.quantity - qty
    db.session.commit()
    flash('Equipment issued successfully.', 'success')
    # Redirect to receipt page for this issue
    return redirect(url_for('storekeeper.issue_receipt', issue_id=issue.id))


# --- Equipment Issue Receipt Route ---
@storekeeper_bp.route('/issue-receipt/<int:issue_id>')
@login_required
def issue_receipt(issue_id):
    issue = IssuedEquipment.query.get_or_404(issue_id)
    # Get storekeeper details
    storekeeper = None
    if issue.issued_by:
        storekeeper = StoreKeeper.query.filter_by(payroll_number=issue.issued_by).first()
        if not storekeeper:
            storekeeper = StoreKeeper.query.filter_by(full_name=issue.issued_by).first()
    if not storekeeper:
        storekeeper = current_user if hasattr(current_user, 'email') else None
    # Parse serials if present
    serials = []
    if issue.serial_numbers:
        try:
            serials = json.loads(issue.serial_numbers)
        except Exception:
            serials = []
    return render_template('issue_receipt.html', issue=issue, serials=serials, storekeeper=storekeeper)


@storekeeper_bp.route('/download-distribution-document/<int:distribution_id>')
@login_required
def download_distribution_document(distribution_id):
    """Download supporting document for a distribution."""
    if not (current_user.is_authenticated and isinstance(current_user, StoreKeeper)):
        abort(403)
    
    distribution = CampusDistribution.query.get_or_404(distribution_id)
    
    if not distribution.document_path:
        flash('No document available for this distribution.', 'warning')
        return redirect(url_for('storekeeper.issued_equipment'))
    
    import os
    from flask import send_file
    
    # Construct the full file path
    file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..',
        'uploads',
        distribution.document_path
    )
    
    # Security check: ensure file exists and path is within uploads directory
    if not os.path.exists(file_path):
        flash('Document file not found.', 'danger')
        return redirect(url_for('storekeeper.issued_equipment'))
    
    # Ensure path is within uploads directory (prevent directory traversal)
    uploads_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..',
        'uploads'
    )
    if not os.path.abspath(file_path).startswith(os.path.abspath(uploads_dir)):
        abort(403)
    
    # Extract filename for download
    filename = os.path.basename(file_path)
    
    try:
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        flash(f'Error downloading document: {str(e)}', 'danger')
        return redirect(url_for('storekeeper.issued_equipment'))

@storekeeper_bp.route('/profile', methods=['POST'])
@login_required
def profile():
    """Update storekeeper profile (email)"""
    if not isinstance(current_user, StoreKeeper):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        email = data.get('email', '').strip() if data else None
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'})
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'error': 'Invalid email format'})
        
        # Check if email already exists for another storekeeper
        existing = StoreKeeper.query.filter(StoreKeeper.id != current_user.id, StoreKeeper.email == email).first()
        if existing:
            return jsonify({'success': False, 'error': 'Email already in use'})
        
        current_user.email = email
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@storekeeper_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change storekeeper password"""
    if not isinstance(current_user, StoreKeeper):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        from werkzeug.security import check_password_hash, generate_password_hash
        
        data = request.get_json()
        current_password = data.get('current_password', '') if data else ''
        new_password = data.get('new_password', '') if data else ''
        
        if not current_password or not new_password:
            return jsonify({'success': False, 'error': 'All fields are required'})
        
        # Verify current password
        if not check_password_hash(current_user.password_hash, current_password):
            return jsonify({'success': False, 'error': 'Current password is incorrect'})
        
        # Validate new password length
        if len(new_password) < 6:
            return jsonify({'success': False, 'error': 'Password must be at least 6 characters'})
        
        # Update password
        current_user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Password changed successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

