from flask import Blueprint, render_template, redirect, url_for, request, flash, session, jsonify, abort
from flask_login import login_required, current_user
from models import StoreKeeper, Equipment, IssuedEquipment, CampusDistribution, Student, Staff, Notification
from extensions import db
from datetime import datetime, UTC
from sqlalchemy import func
from Utils.student_checks import has_unreturned_items
import json

storekeeper_bp = Blueprint('storekeeper', __name__, url_prefix='/storekeeper')

@storekeeper_bp.route('/api/notifications/unread-count')
@login_required
def unread_notifications_count():
    """API endpoint to get unread notifications count for storekeeper"""
    unread = Notification.query.filter_by(recipient_role='storekeeper', recipient_id=current_user.id, is_read=False).count()
    return jsonify({'count': unread})

@storekeeper_bp.route('/api/notifications')
@login_required
def get_notifications():
    """API endpoint to get all unread notifications for storekeeper"""
    notifs = Notification.query.filter_by(recipient_role='storekeeper', recipient_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(10).all()
    return jsonify([
        {'id': n.id, 'message': n.message, 'url': n.url, 'created_at': n.created_at.isoformat()}
        for n in notifs
    ])

@storekeeper_bp.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    """API endpoint to mark a notification as read"""
    notif = Notification.query.get(notif_id)
    if notif:
        notif.is_read = True
        db.session.commit()
    return jsonify({'success': True})

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
    # Get all issues issued by this storekeeper and group them by recipient and issue date (same day)
    all_issues = IssuedEquipment.query.filter_by(issued_by=current_user.payroll_number).order_by(IssuedEquipment.date_issued.desc()).all()

    # Group key: (recipient_key, date)
    grouped = {}
    for it in all_issues:
        recipient_key = it.student_id or it.staff_payroll or 'unknown'
        issue_date = it.date_issued.date() if it.date_issued else None
        key = (recipient_key, issue_date)
        if key not in grouped:
            grouped[key] = {
                'recipient_key': recipient_key,
                'date': issue_date,
                'issues': [],
                'first_issue_id': it.id
            }
        grouped[key]['issues'].append(it)

    # Convert to list and sort by date desc, then by recipient
    receipts = []
    for (recipient_key, issue_date), data in grouped.items():
        # Determine recipient display name
        student = Student.query.filter_by(id=recipient_key).first() if recipient_key and len(recipient_key) < 20 else None
        staff = None if student else Staff.query.filter_by(payroll_number=recipient_key).first()
        recipient_name = student.name if student else (staff.name if staff else None)

        # Build equipment summary for this receipt
        equipment_summary = []
        total_qty = 0
        for it in data['issues']:
            name = it.equipment.name if it.equipment else f"ID:{it.equipment_id}"
            equipment_summary.append({'name': name, 'quantity': it.quantity})
            total_qty += it.quantity

        receipts.append({
            'receipt_no': f"ISS-{data['first_issue_id']:04d}",
            'recipient_type': 'Student' if student else ('Staff' if staff else 'Unknown'),
            'recipient_id': recipient_key,
            'recipient_name': recipient_name or '—',
            'equipment': equipment_summary,
            'total_qty': total_qty,
            'date_issued': data['date'],
            'first_issue_id': data['first_issue_id']
        })

    # sort receipts by date desc (safe handling if date_issued is None)
    receipts = sorted(receipts, key=lambda r: (r['date_issued'].toordinal() if r['date_issued'] else 0), reverse=True)

    return render_template('storekeeper_receipts.html', receipts=receipts)


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
    
    # Count damaged and lost items from return_conditions
    returned_items = IssuedEquipment.query.filter(
        IssuedEquipment.issued_by == current_user.payroll_number,
        IssuedEquipment.status.in_(['Returned', 'Partial Return']),
        IssuedEquipment.return_conditions.isnot(None)
    )
    if equipment_ids:
        returned_items = returned_items.filter(IssuedEquipment.equipment_id.in_(equipment_ids))
    returned_items = returned_items.all()
    
    total_damaged = 0
    total_lost = 0
    for item in returned_items:
        if item.return_conditions:
            try:
                conditions = json.loads(item.return_conditions)
                total_damaged += sum(1 for c in conditions.values() if c == 'Damaged')
                total_lost += sum(1 for c in conditions.values() if c == 'Lost')
            except:
                pass
    
    # Get unread notifications count for this storekeeper
    unread_count = Notification.query.filter_by(recipient_role='storekeeper', recipient_id=current_user.id, is_read=False).count()
    
    return render_template('storekeeper_dashboard.html',
                           total_equipment=total_equipment,
                           total_active=total_active,
                           total_issued=total_issued,
                           total_damaged=total_damaged,
                           total_lost=total_lost,
                           low_stock=low_stock,
                           due_items=due_items,
                           current_user=current_user,
                           campus_name=current_user.campus.name if current_user.campus else 'Unknown',
                           unread_notifications=unread_count)


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
    # Get all issued equipment created by this storekeeper, listed separately
    issuer_identifier = getattr(current_user, 'payroll_number', None)
    if issuer_identifier:
        all_issued = IssuedEquipment.query.filter_by(issued_by=issuer_identifier).order_by(IssuedEquipment.date_issued.desc()).all()
    else:
        all_issued = []

    return render_template('issued_equipment.html', issued=all_issued)


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
    """Return Equipment module: display all issued equipment from this storekeeper's campus"""
    if request.method == 'POST':
        # Handle return of selected items (same logic as before)
        selected_serials = request.form.getlist('selected_serials')
        if not selected_serials:
            flash('No items selected for return.', 'warning')
            return redirect(url_for('storekeeper.return_equipment'))
        
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
                    # Partial return - update status to 'Partial Return'
                    existing_conditions = {}
                    if issue.return_conditions:
                        try:
                            existing_conditions = json.loads(issue.return_conditions)
                        except:
                            pass
                    
                    # Merge new conditions with existing ones
                    existing_conditions.update(conditions)
                    issue.return_conditions = json.dumps(existing_conditions)
                    issue.status = 'Partial Return'
                    
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
        
        return redirect(url_for('storekeeper.return_equipment'))
    
    # Check if showing detailed return for a specific recipient
    return_recipient_id = request.args.get('return_recipient', '').strip()
    
    if return_recipient_id:
        # Get all items for this recipient
        issued_query = IssuedEquipment.query.filter(
            db.or_(
                IssuedEquipment.student_id == return_recipient_id,
                IssuedEquipment.staff_payroll == return_recipient_id
            ),
            IssuedEquipment.status.in_(['Issued', 'Partial Return'])
        ).order_by(IssuedEquipment.date_issued.desc()).all()
        
        # Create detailed display items with parsed serials
        display_items = []
        for item in issued_query:
            # Get already returned serials from return_conditions
            returned_serials = set()
            if item.return_conditions:
                try:
                    returned_conditions = json.loads(item.return_conditions)
                    returned_serials = set(returned_conditions.keys())
                except:
                    pass
            
            if item.serial_numbers:
                try:
                    serials = json.loads(item.serial_numbers)
                except:
                    serials = []
            else:
                serials = []
            
            if serials:
                # For items with serials, create one entry per serial (excluding already returned ones)
                for serial in serials:
                    # Skip serials that have already been returned
                    if serial in returned_serials:
                        continue
                    display_items.append({
                        'issue': item,
                        'serial': serial,
                        'equipment_name': item.equipment.name if item.equipment else item.equipment_id,
                        'recipient_name': item.student.name if item.student else (item.staff.name if item.staff else 'Unknown'),
                        'recipient_id': item.student_id or item.staff_payroll
                    })
            else:
                # For items without serials, create one entry
                display_items.append({
                    'issue': item,
                    'serial': None,
                    'equipment_name': item.equipment.name if item.equipment else item.equipment_id,
                    'recipient_name': item.student.name if item.student else (item.staff.name if item.staff else 'Unknown'),
                    'recipient_id': item.student_id or item.staff_payroll
                })
        
        return render_template('return_equipment.html', display_items=display_items, show_detail=True, return_recipient_id=return_recipient_id)
    
    # GET: Show all issued equipment from this storekeeper's campus - grouped by recipient
    # Get aggregated equipment distributed to this storekeeper's campus only
    aggregated = aggregate_distributions(current_user.campus_id)
    campus_equipment_ids = list(aggregated.keys())
    
    # Get all issued equipment for this campus
    issued_query = IssuedEquipment.query.filter(
        IssuedEquipment.equipment_id.in_(campus_equipment_ids) if campus_equipment_ids else False,
        IssuedEquipment.status.in_(['Issued', 'Partial Return'])
    ).order_by(IssuedEquipment.date_issued.desc()).all()
    
    # If no campus equipment, get issued items anyway
    if not campus_equipment_ids:
        issued_query = IssuedEquipment.query.filter(
            IssuedEquipment.status.in_(['Issued', 'Partial Return'])
        ).order_by(IssuedEquipment.date_issued.desc()).all()
    
    # Group by recipient
    from collections import defaultdict
    recipient_groups = defaultdict(list)
    for item in issued_query:
        recipient_key = item.student_id or item.staff_payroll
        if recipient_key:
            recipient_groups[recipient_key].append(item)
    
    # Create aggregated display items per recipient
    display_items = []
    for recipient_key, items in recipient_groups.items():
        # Get recipient info from first item
        first_item = items[0]
        recipient_name = first_item.student.name if first_item.student else (first_item.staff.name if first_item.staff else 'Unknown')
        recipient_type = 'Student' if first_item.student else 'Staff'
        
        # Count total items
        total_count = 0
        equipment_names = []
        seen_equipment = set()
        
        for item in items:
            if item.serial_numbers:
                try:
                    serials = json.loads(item.serial_numbers)
                    total_count += len(serials)
                except:
                    total_count += item.quantity
            else:
                total_count += item.quantity
            
            eq_name = item.equipment.name if item.equipment else str(item.equipment_id)
            if eq_name not in seen_equipment:
                equipment_names.append(eq_name)
                seen_equipment.add(eq_name)
        
        equipment_display = ', '.join(equipment_names) if len(equipment_names) <= 3 else f"{', '.join(equipment_names[:3])}, +{len(equipment_names)-3} more"
        
        display_items.append({
            'recipient_id': recipient_key,
            'recipient_name': recipient_name,
            'recipient_type': recipient_type,
            'equipment_display': equipment_display,
            'total_count': total_count,
            'issue_count': len(items)
        })
    
    # Sort by most recent date
    display_items = sorted(display_items, key=lambda x: x['recipient_name'])
    
    return render_template('return_equipment.html', display_items=display_items, show_detail=False)


@storekeeper_bp.route('/return/<int:issue_id>', methods=['GET', 'POST'])
@login_required
def return_item(issue_id):
    issue = IssuedEquipment.query.get_or_404(issue_id)
    # Allow returns for 'Issued' and 'Partial Return' statuses
    if issue.status == 'Returned':
        flash('This item has already been returned.', 'warning')
        return redirect(url_for('storekeeper.issued_equipment'))
    
    if issue.status not in ('Issued', 'Partial Return'):
        flash('This item cannot be returned in its current status.', 'warning')
        return redirect(url_for('storekeeper.issued_equipment'))

    # Parse serial numbers and filter out already-returned ones
    serials = []
    if issue.serial_numbers:
        try:
            serials = json.loads(issue.serial_numbers)
        except:
            serials = []

    # Filter out already-returned serials
    already_returned = set()
    if issue.return_conditions:
        try:
            cond_data = json.loads(issue.return_conditions)
            if isinstance(cond_data, dict) and 'conditions' in cond_data:
                already_returned = set(cond_data.get('conditions', {}).keys())
            elif isinstance(cond_data, dict):
                already_returned = set(cond_data.keys()) - {'all', 'quantity'}
        except:
            pass
    
    # Filter serials to show only those not yet returned
    remaining_serials = [s for s in serials if s not in already_returned]

    if request.method == 'GET':
        # If no serials remain and quantity is 0 for non-serial, show message
        if not remaining_serials and issue.quantity <= 0:
            flash('All items for this issue have already been returned.', 'info')
            return redirect(url_for('storekeeper.issued_equipment'))
        
        return render_template('return_form.html', issue=issue, serials=remaining_serials)

    condition = request.form.get('condition')
    returned_serials = request.form.getlist('returned_serials')
    
    # Handle serial and non-serial returns, allowing partial serial returns with quantities
    equipment = Equipment.query.get_or_404(issue.equipment_id)

    if serials:
        # Ensure at least one serial was selected
        if not returned_serials:
            flash('No serials selected for return.', 'warning')
            return redirect(url_for('storekeeper.return_item', issue_id=issue_id))

        # Collect conditions and quantities for the newly returned serials
        new_conditions = {}
        new_quantities = {}
        total_returned = 0
        
        for serial in returned_serials:
            cond = request.form.get(f'condition_{serial}')
            if not cond or cond not in ('Good', 'Damaged', 'Lost'):
                flash(f'Please select a valid return condition for serial number {serial}.', 'danger')
                return redirect(url_for('storekeeper.return_item', issue_id=issue_id))
            
            # Each serial counts as 1 item
            new_conditions[serial] = cond
            new_quantities[serial] = 1
            total_returned += 1

        # Merge with any existing return conditions and quantities
        existing_conditions = {}
        existing_quantities = {}
        if issue.return_conditions:
            try:
                cond_data = json.loads(issue.return_conditions)
                # Handle both old format (conditions only) and new format (with quantities)
                if isinstance(cond_data, dict) and 'conditions' in cond_data:
                    existing_conditions = cond_data.get('conditions', {})
                    existing_quantities = cond_data.get('quantities', {})
                else:
                    existing_conditions = cond_data
            except:
                existing_conditions = {}

        # Update issue.return_conditions with merged data
        existing_conditions.update(new_conditions)
        existing_quantities.update(new_quantities)
        issue.return_conditions = json.dumps({
            'conditions': existing_conditions,
            'quantities': {k: v for k, v in existing_quantities.items()}
        })

        # Determine status based on return completeness
        if len(existing_conditions) >= len(serials):
            # All serials have been returned
            print(f"DEBUG: All returned. len(conditions)={len(existing_conditions)}, len(serials)={len(serials)}")
            issue.status = 'Returned'
            issue.date_returned = datetime.now(UTC)
        else:
            # Some but not all serials have been returned
            print(f"DEBUG: Partial. len(conditions)={len(existing_conditions)}, len(serials)={len(serials)}, conditions={existing_conditions.keys()}, serials={serials}")
            issue.status = 'Partial Return'
            # Don't set date_returned yet

        # Update equipment counts based on newly returned serials with quantities
        good_count = sum(qty for serial, qty in new_quantities.items() if new_conditions[serial] == 'Good')
        damaged_count = sum(qty for serial, qty in new_quantities.items() if new_conditions[serial] == 'Damaged')
        lost_count = sum(qty for serial, qty in new_quantities.items() if new_conditions[serial] == 'Lost')

    else:
        # Non-serial items: support partial quantity returns
        condition = request.form.get('condition')
        if not condition or condition not in ('Good', 'Damaged', 'Lost'):
            flash('Please select a valid return condition.', 'danger')
            return redirect(url_for('storekeeper.return_item', issue_id=issue_id))

        # Get quantity to return (default to total issue quantity)
        try:
            qty_to_return = int(request.form.get('quantity_all', issue.quantity))
            if qty_to_return < 0:
                qty_to_return = issue.quantity
            if qty_to_return > issue.quantity:
                qty_to_return = issue.quantity
        except:
            qty_to_return = issue.quantity

        # Only mark as fully returned if returning entire quantity
        if qty_to_return >= issue.quantity:
            issue.status = 'Returned'
            issue.date_returned = datetime.now(UTC)
            return_qty = issue.quantity
        else:
            # Partial return: update quantity in issue to reflect remaining items
            issue.quantity -= qty_to_return
            issue.status = 'Partial Return'
            return_qty = qty_to_return
        
        issue.return_conditions = json.dumps({'all': condition, 'quantity': return_qty})

        if condition == 'Good':
            good_count = qty_to_return
            damaged_count = 0
            lost_count = 0
        elif condition == 'Damaged':
            good_count = 0
            damaged_count = qty_to_return
            lost_count = 0
        else:
            good_count = 0
            damaged_count = 0
            lost_count = qty_to_return

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
    confirm_unreturned = request.form.get('confirm_unreturned') == 'true'
    
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
        if has_unreturned and not confirm_unreturned:
            # Parse serial numbers for each unreturned item
            for item in unreturned_items:
                serials = []
                if item.serial_numbers:
                    try:
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
    # Redirect to combined receipt for this recipient
    recipient_id = student_id if person_type == 'student' else staff_payroll
    return redirect(url_for('storekeeper.issue_receipt', recipient_id=recipient_id))


# --- Equipment Issue Receipt Route ---
@storekeeper_bp.route('/issue-receipt/<int:issue_id>')
@storekeeper_bp.route('/issue-receipt/recipient/<path:recipient_id>')
@login_required
def issue_receipt(issue_id=None, recipient_id=None):
    """Show receipt for issued equipment. Can show single issue by ID or all issues for a recipient today."""
    if issue_id:
        # Legacy: single issue by ID
        issue = IssuedEquipment.query.get_or_404(issue_id)
        issues = [issue]
        recipient_key = issue.student_id or issue.staff_payroll
    elif recipient_id:
        # Show all issues for this recipient for a given date (query param `date=YYYY-MM-DD`) or for today by default
        from datetime import datetime, timedelta
        date_str = request.args.get('date')
        if date_str:
            try:
                day = datetime.strptime(date_str, '%Y-%m-%d')
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
            except Exception:
                day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
        else:
            day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

        issues = IssuedEquipment.query.filter(
            db.or_(
                IssuedEquipment.student_id == recipient_id,
                IssuedEquipment.staff_payroll == recipient_id
            ),
            IssuedEquipment.date_issued >= day_start,
            IssuedEquipment.date_issued < day_end,
            IssuedEquipment.issued_by == current_user.payroll_number
        ).order_by(IssuedEquipment.date_issued.desc()).all()
        if not issues:
            flash('No issues found for this recipient on the selected date.', 'warning')
            return redirect(url_for('storekeeper.issue'))
        recipient_key = recipient_id
    else:
        abort(400)
    
    # Get recipient info (student or staff)
    student = Student.query.filter_by(id=recipient_key).first() if len(recipient_key) < 20 else None
    staff = Staff.query.filter_by(payroll_number=recipient_key).first() if not student else None
    
    # Get issuer name
    issuer_name = 'Unknown'
    if issues and issues[0].issued_by:
        sk = StoreKeeper.query.filter_by(payroll_number=issues[0].issued_by).first()
        if sk:
            issuer_name = sk.full_name
        else:
            issuer_name = issues[0].issued_by
    
    # Parse serials for each issue
    for issue in issues:
        serials = []
        if issue.serial_numbers:
            try:
                serials = json.loads(issue.serial_numbers)
            except Exception:
                serials = []
        issue.serials = serials
    
    return render_template('issue_receipt.html', issues=issues, student=student, staff=staff, issuer_name=issuer_name)


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


@storekeeper_bp.route('/damage-clearance')
@login_required
def damage_clearance():
    """View damaged/lost equipment awaiting clearance"""
    # Get all returned equipment with Damaged or Lost conditions from this storekeeper's campus
    aggregated = aggregate_distributions(current_user.campus_id)
    campus_equipment_ids = list(aggregated.keys())
    
    # Get all returned items with damaged or lost conditions
    returned_query = IssuedEquipment.query.filter(
        IssuedEquipment.status.in_(['Returned', 'Partial Return']),
        IssuedEquipment.return_conditions.isnot(None)
    )
    if campus_equipment_ids:
        returned_query = returned_query.filter(IssuedEquipment.equipment_id.in_(campus_equipment_ids))
    
    returned_items = returned_query.order_by(IssuedEquipment.date_returned.desc()).all()
    
    # Filter to only items with Damaged or Lost conditions
    damage_items = []
    for item in returned_items:
        if item.return_conditions:
            try:
                conditions = json.loads(item.return_conditions)
                has_damage = any(c in ('Damaged', 'Lost') for c in conditions.values())
                if has_damage:
                    # Extract damaged/lost items
                    damage_list = []
                    for serial, condition in conditions.items():
                        if condition in ('Damaged', 'Lost'):
                            damage_list.append({
                                'serial': serial,
                                'condition': condition
                            })

                    # Skip items that have been escalated to admin (storekeeper shouldn't act on them)
                    if item.damage_clearance_status == 'Escalated':
                        continue

                    # Parse any admin notes or attached document path from damage_clearance_notes
                    admin_notes = item.damage_clearance_notes or ''
                    doc_path = None
                    if admin_notes:
                        try:
                            # Look for a line containing 'Attached document:' and extract the path
                            parts = [l.strip() for l in admin_notes.splitlines() if l.strip()]
                            remaining_lines = []
                            for line in parts:
                                if 'Attached document:' in line:
                                    # everything after the colon is the stored path
                                    doc_path = line.split('Attached document:', 1)[1].strip()
                                else:
                                    remaining_lines.append(line)
                            admin_text = '\n'.join(remaining_lines)
                        except Exception:
                            admin_text = admin_notes
                    else:
                        admin_text = ''

                    item._admin_notes = admin_text
                    item._document_path = doc_path
                    item._damage_list = damage_list
                    item._recipient_name = item.student.name if item.student else (item.staff.name if item.staff else 'Unknown')
                    item._recipient_type = 'Student' if item.student else 'Staff'
                    # Flag needs-review items for highlighting
                    item._needs_review = (item.damage_clearance_status == 'Needs Review')
                    damage_items.append(item)
            except:
                pass
    
    # Sort so 'Needs Review' items appear first
    damage_items = sorted(damage_items, key=lambda it: (not getattr(it, '_needs_review', False), it.date_returned or datetime.now()))
    return render_template('damage_clearance.html', damage_items=damage_items)


@storekeeper_bp.route('/damage-clearance/<int:issue_id>', methods=['POST'])
@login_required
def process_damage_clearance(issue_id):
    """Process damage/loss clearance: either clear (Repaired/Replaced) or escalate to admin"""
    issue = IssuedEquipment.query.get_or_404(issue_id)
    
    action = request.form.get('action')
    clearance_status = request.form.get('clearance_status')
    notes = request.form.get('notes', '').strip()
    
    if action == 'clear':
        # Mark as cleared (Repaired or Replaced)
        if clearance_status not in ('Repaired', 'Replaced'):
            flash('Invalid clearance status.', 'danger')
            return redirect(url_for('storekeeper.damage_clearance'))
        
        issue.damage_clearance_status = clearance_status
        issue.damage_clearance_notes = notes
        db.session.commit()
        flash(f'Equipment marked as {clearance_status}. Recipient may now clear.', 'success')
        
    elif action == 'escalate':
        # Escalate to admin
        issue.damage_clearance_status = 'Escalated'
        issue.damage_clearance_notes = notes
        # Create a notification for admins (broadcast)
        try:
            from models import Notification
            notif = Notification(recipient_role='admin', recipient_id=None,
                                 message=f"Issue {issue.id} escalated by {current_user.full_name or current_user.payroll_number}",
                                 url=url_for('admin.escalated_damage'))
            db.session.add(notif)
        except Exception:
            pass
        db.session.commit()
        flash('Issue escalated to admin for further action.', 'info')
    
    else:
        flash('Invalid action.', 'danger')
    
    return redirect(url_for('storekeeper.damage_clearance'))

