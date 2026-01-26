from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify
from flask_login import login_required, current_user
from models import StoreKeeper, Equipment, IssuedEquipment
from extensions import db
from datetime import datetime, UTC
from sqlalchemy import func
from Utils.student_checks import has_unreturned_items
import json

storekeeper_bp = Blueprint('storekeeper', __name__, url_prefix='/storekeeper')

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
    total_equipment = Equipment.query.count()
    total_active = Equipment.query.filter_by(is_active=True).count()
    total_issued = IssuedEquipment.query.filter_by(status='Issued').count()
    low_stock = Equipment.query.filter(Equipment.quantity <= 5).order_by(Equipment.quantity.asc()).all()
    today = datetime.now().date()
    due_items = IssuedEquipment.query.filter(
        IssuedEquipment.status == 'Issued',
        IssuedEquipment.expected_return != None,
        func.date(IssuedEquipment.expected_return) <= today
    ).order_by(IssuedEquipment.expected_return.asc()).all()
    return render_template('storekeeper_dashboard.html',
                           total_equipment=total_equipment,
                           total_active=total_active,
                           total_issued=total_issued,
                           low_stock=low_stock,
                           due_items=due_items,
                           current_user=current_user)


@storekeeper_bp.route('/equipment')
@login_required
def equipment():
    all_equipment = Equipment.query.order_by(Equipment.category.asc(), Equipment.name.asc()).all()
    return render_template('storekeeper_equipment.html', equipment=all_equipment)


@storekeeper_bp.route('/issued-equipment')
@login_required
def issued_equipment():
    issued = IssuedEquipment.query.order_by(IssuedEquipment.date_issued.desc()).all()
    return render_template('issued_equipment.html', issued=issued)


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
        IssuedEquipment.staff_name.label('name'),
        db.literal('Staff').label('type')
    ).filter(
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
                    from Utils.clearance_integration import update_clearance_status
                    update_clearance_status(student_id)
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
    
    if recipient_id:
        # Find issued equipment for this recipient
        issued_items = IssuedEquipment.query.filter(
            db.or_(
                IssuedEquipment.student_id.ilike(f"%{recipient_id}%"),
                IssuedEquipment.staff_payroll.ilike(f"%{recipient_id}%")
            ),
            IssuedEquipment.status == 'Issued'
        ).order_by(IssuedEquipment.date_issued.desc()).all()
        
        # Determine recipient type and name
        if issued_items:
            first_item = issued_items[0]
            if first_item.student_id:
                recipient_type = "Student"
                recipient_name = first_item.student_name
            elif first_item.staff_payroll:
                recipient_type = "Staff/Trainer"
                recipient_name = first_item.staff_name
        
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
            from Utils.clearance_integration import update_clearance_status
            update_clearance_status(issue.student_id)
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
        equipment = Equipment.query.filter_by(is_active=True).order_by(Equipment.name).all()
        issued = IssuedEquipment.query.order_by(IssuedEquipment.date_issued.desc()).all()
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
        for issue in IssuedEquipment.query.filter(IssuedEquipment.serial_number.isnot(None)):
            try:
                serials = json.loads(issue.serial_number)
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
            items_list = ", ".join([
                f"{item.equipment.name} (Due: {item.expected_return.strftime('%Y-%m-%d') if item.expected_return else 'No due date'})"
                for item in unreturned_items
            ])
            flash(f'Student has unreturned items: {items_list}. Please return these items first.', 'danger')
            return redirect(url_for('storekeeper.issue'))
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
    if not expected_return_str:
        flash('Expected return date is required.', 'danger')
        return redirect(url_for('storekeeper.issue'))
    try:
        eq = db.session.get(Equipment, int(equipment_id))
    except Exception:
        eq = None
    if not eq:
        flash('Selected equipment not found.', 'danger')
        return redirect(url_for('storekeeper.issue'))
    if eq.quantity < qty:
        flash(f'Not enough items available. Available: {eq.quantity}', 'danger')
        return redirect(url_for('storekeeper.issue'))
    try:
        expected_return = datetime.strptime(expected_return_str, '%Y-%m-%d')
    except ValueError:
        flash('Invalid expected return date format.', 'danger')
        return redirect(url_for('storekeeper.issue'))
    today_date = datetime.now().date()
    if expected_return.date() < today_date:
        flash('Expected return date cannot be in the past. Please select today or a future date.', 'danger')
        return redirect(url_for('storekeeper.issue'))
    issue = IssuedEquipment(
        # Use empty strings for student fields when issuing to staff to avoid NULL constraint errors
        student_id=student_id if person_type=='student' else '',
        student_name=student_name if person_type=='student' else '',
        student_email=student_email if person_type=='student' else '',
        student_phone=student_phone if person_type=='student' else '',
        staff_payroll=staff_payroll if person_type=='staff' else None,
        staff_name=staff_name if person_type=='staff' else None,
        staff_email=staff_email if person_type=='staff' else None,
        equipment_id=eq.id, quantity=qty,
        expected_return=expected_return,
        serial_numbers=json.dumps(serial_numbers) if serial_numbers else None
    )
    db.session.add(issue)
    # store who issued this item (username of the current user)
    try:
        issue.issued_by = current_user.username
    except Exception:
        issue.issued_by = None
    eq.quantity = eq.quantity - qty
    db.session.commit()
    flash('Equipment issued successfully.', 'success')
    return redirect(url_for('storekeeper.issue'))
