from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify, session, abort
from flask_login import login_required, current_user
from extensions import db
from models import Admin, StoreKeeper, Equipment, IssuedEquipment, Clearance, Student, Staff, SatelliteCampus, EquipmentCategory, CampusDistribution
from datetime import datetime, UTC, timedelta
import uuid
from Utils.clearance_integration import get_clearance_status
import csv
import io
import re
import json
from sqlalchemy import distinct, func
from werkzeug.utils import secure_filename

# Optional PDF parsing support
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except Exception:
    pdfplumber = None
    PDFPLUMBER_AVAILABLE = False

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.before_request
def _require_admin():
    # Prevent non-admin users from accessing admin routes
    if not current_user.is_authenticated:
        return
    if not isinstance(current_user, Admin):
        # if a storekeeper is logged in, redirect them to their dashboard
        from flask import redirect, url_for
        return redirect(url_for('storekeeper.dashboard'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    total_equipment = Equipment.query.count()
    total_satellite_campuses = SatelliteCampus.query.filter_by(is_active=True).count()

    # Calculate cleared students dynamically
    from Utils.clearance_integration import get_clearance_status
    students = Student.query.all()
    total_cleared = sum(1 for student in students if get_clearance_status(student.id) == 'Cleared')

    # Additional overview statistics
    total_returned = IssuedEquipment.query.filter(IssuedEquipment.status == 'Returned').count()
    returned_good = IssuedEquipment.query.filter(
        IssuedEquipment.status == 'Returned',
        IssuedEquipment.return_conditions == 'Good'
    ).count()

    # Distribution metrics (satellite campus distributions)
    total_distributions_count = CampusDistribution.query.count()
    # Sum of quantities distributed to campuses
    total_distributed_quantity = db.session.query(func.coalesce(func.sum(CampusDistribution.quantity), 0)).scalar()
    returned_damaged = IssuedEquipment.query.filter(
        IssuedEquipment.status == 'Returned',
        IssuedEquipment.return_conditions == 'Damaged'
    ).count()
    returned_lost = IssuedEquipment.query.filter(
        IssuedEquipment.status == 'Returned',
        IssuedEquipment.return_conditions == 'Lost'
    ).count()

    # Total recipients (students + staff)
    total_students = Student.query.count()
    total_staff = Staff.query.count()
    total_recipients = total_students + total_staff

    # Find due issued items (due date is today or earlier and still Issued)
    today = datetime.now().date()
    due_items_q = IssuedEquipment.query.filter(
        IssuedEquipment.status == 'Issued',
        IssuedEquipment.expected_return != None,
        func.date(IssuedEquipment.expected_return) <= today
    ).order_by(IssuedEquipment.expected_return.asc())

    due_items = due_items_q.all()

    # Build flat list of all due items with recipient details
    all_due_items = []
    for it in due_items:
        # Get recipient details through relationships
        if it.student:
            recipient_id = it.student.id
            recipient_name = it.student.name
            recipient_email = it.student.email
            recipient_phone = it.student.phone
            recipient_type = 'student'
        elif it.staff:
            recipient_id = it.staff.payroll_number
            recipient_name = it.staff.name
            recipient_email = it.staff.email
            recipient_phone = None  # Staff don't have phone in our model
            recipient_type = 'staff'
        else:
            # Fallback for items without proper relationships
            recipient_id = it.staff_payroll or it.student_id or 'Unknown'
            recipient_name = 'Unknown'
            recipient_email = None
            recipient_phone = None
            recipient_type = 'unknown'
            
        all_due_items.append({
            'recipient_id': recipient_id,
            'recipient_name': recipient_name,
            'recipient_email': recipient_email,
            'recipient_phone': recipient_phone,
            'recipient_type': recipient_type,
            'equipment_name': it.equipment.name if it.equipment else str(it.equipment_id),
            'equipment_id': it.equipment_id,
            'quantity': it.quantity,
            'expected_return': it.expected_return
        })

    due_count = len(due_items)

    return render_template('dashboard.html',
                           total_equipment=total_equipment,
                           total_satellite_campuses=total_satellite_campuses,
                           total_cleared=total_cleared,
                           total_returned=total_returned,
                           returned_good=returned_good,
                           returned_damaged=returned_damaged,
                           returned_lost=returned_lost,
                           total_recipients=total_recipients,
                           due_count=due_count,
                           all_due_items=all_due_items,
                           total_distributions_count=total_distributions_count,
                           total_distributed_quantity=total_distributed_quantity)

@admin_bp.route('/equipment', methods=['GET', 'POST'])
@login_required
def equipment():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        category_code = request.form['category_code']
        quantity = request.form['quantity']
        
        # Prefer updating an existing equipment that matches both category_code and name.
        try:
            qty = int(quantity)
        except Exception:
            qty = 0

        existing_exact = Equipment.query.filter_by(category_code=category_code.upper(), name=name).first()
        if existing_exact:
            existing_exact.quantity = (existing_exact.quantity or 0) + qty
            db.session.add(existing_exact)
            db.session.commit()
            flash(f'Existing equipment "{name}" updated. Quantity increased by {qty}.', 'success')
        else:
            # No exact match; create a new equipment record under this category code
            new_item = Equipment(
                name=name,
                category=category,
                category_code=category_code.upper(),  # Store in uppercase for consistency
                quantity=qty,
                serial_number=uuid.uuid4().hex
            )
            db.session.add(new_item)
            db.session.commit()
            flash('Equipment added successfully!', 'success')
        return redirect(url_for('admin.equipment'))
    # Sort by category_code first, then category, then name for proper grouping in template
    all_equipment = Equipment.query.order_by(Equipment.category_code.asc(), Equipment.category.asc(), Equipment.name.asc()).all()
    return render_template('equipment.html', equipment=all_equipment)


@admin_bp.route('/equipment/export-csv')
@login_required
def equipment_export_csv():
    """Export all received equipment as CSV, grouped by category code like the template."""
    # Sort by category_code first, then category, then name (same as template)
    all_equipment = Equipment.query.order_by(Equipment.category_code.asc(), Equipment.category.asc(), Equipment.name.asc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    # Write headers
    writer.writerow(['Category Code', 'Category Name', 'Equipment Name', 'Quantity', 'Date Received'])
    
    # Group equipment by category_code
    from itertools import groupby
    for code, group in groupby(all_equipment, key=lambda x: x.category_code):
        group_list = list(group)
        for index, item in enumerate(group_list):
            # Only write category code and name for the first item in each group
            if index == 0:
                writer.writerow([
                    item.category_code,
                    item.category,
                    item.name,
                    item.quantity,
                    item.date_received.strftime('%Y-%m-%d') if item.date_received else 'N/A'
                ])
            else:
                # For subsequent items in the group, leave category code and name blank
                writer.writerow([
                    '',
                    '',
                    item.name,
                    item.quantity,
                    item.date_received.strftime('%Y-%m-%d') if item.date_received else 'N/A'
                ])
    
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', 
                   headers={"Content-Disposition": "attachment;filename=received_equipment.csv"})


@admin_bp.route('/equipment/upload', methods=['POST'])
@login_required
def equipment_upload():
    """Handle CSV upload for bulk adding/updating equipment.

    Expected CSV columns: name,category,category_code,quantity
    If category_code matches existing equipment, increment quantity; otherwise create new record.
    """
    # determine requested action (preview or confirm)
    action = request.form.get('action')

    # File may be absent when confirming a previously previewed upload; allow that case
    file = request.files.get('csv_file')

    # If admin is confirming and we have preview data in session, commit that without needing the file
    if not file and action == 'confirm' and session.get('equipment_upload_preview'):
        raw = session.pop('equipment_upload_preview', None)
        try:
            parsed_rows = json.loads(raw)
        except Exception:
            try:
                parsed_rows = eval(raw)  # fallback if stored as python repr
            except Exception:
                parsed_rows = []

        # Commit parsed rows to DB
        created = 0
        updated = 0
        skipped = 0
        errors = []

        for entry in parsed_rows:
            if not entry.get('valid'):
                skipped += 1
                errors.append(f"Row {entry.get('row')}: {entry.get('error')}")
                continue

            name = entry['name']
            category = entry.get('category', '')
            category_code = entry.get('category_code', '')
            qty = int(entry.get('quantity', 0) or 0)
            # If any equipment with the same category_code exists, update it
            existing_by_code = Equipment.query.filter_by(category_code=category_code).first()
            if existing_by_code:
                existing_by_code.quantity = (existing_by_code.quantity or 0) + max(0, qty)
                db.session.add(existing_by_code)
                updated += 1
            else:
                new_item = Equipment(
                    name=name,
                    category=category or '',
                    category_code=category_code,
                    quantity=max(0, qty),
                    serial_number=uuid.uuid4().hex
                )
                db.session.add(new_item)
                created += 1

        try:
            db.session.commit()
            flash(f'CSV import finished. Created: {created}, Updated: {updated}, Skipped: {skipped}', 'success')
            if errors:
                flash('Some rows had issues: ' + '; '.join(errors), 'warning')
        except Exception as e:
            db.session.rollback()
            flash('Error importing CSV: ' + str(e), 'danger')

        return redirect(url_for('admin.equipment'))

    # If we reach here, we need a file to proceed (either new preview or direct commit with file)
    if not file:
        flash('No file uploaded.', 'danger')
        return redirect(url_for('admin.equipment'))

    # otherwise proceed with the normal file-based parsing flow
    filename = secure_filename(file.filename) if file else ''
    lower = filename.lower() if filename else ''

    import csv
    import io

    reader = None

    # Helper: normalize header key
    def normalize_key(k: str) -> str:
        if not k:
            return ''
        nk_raw = k.strip().lower()
        nk = re.sub(r'[^0-9a-z]+', '_', nk_raw)
        nk = re.sub(r'_+', '_', nk).strip('_')
        # Map common synonyms
        if nk in ('equipment_name', 'equipment name', 'item_name', 'item'):
            return 'name'
        if nk in ('category_code', 'category code', 'categorycode', 'cat_code', 'code'):
            return 'category_code'
        if nk in ('qty', 'quantity', 'count'):
            return 'quantity'
        return nk

    # Create reader for CSV
    if lower.endswith('.csv') or file.mimetype == 'text/csv':
        try:
            raw = file.stream.read()
            try:
                text = raw.decode('utf-8-sig')
            except Exception:
                text = raw.decode('utf-8', errors='replace')

            # Try to sniff dialect
            try:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(text[:4096])
            except Exception:
                dialect = csv.get_dialect('excel')

            stream = io.StringIO(text)
            reader = csv.DictReader(stream, dialect=dialect, restval='')
        except Exception:
            flash('Failed to read CSV file. Ensure it is a valid CSV (UTF-8).', 'danger')
            return redirect(url_for('admin.equipment'))

    # Handle PDF upload - attempt to extract table using pdfplumber
    elif lower.endswith('.pdf') or file.mimetype == 'application/pdf':
        if not PDFPLUMBER_AVAILABLE:
            flash('PDF import is not available on this server. Please install pdfplumber (pip install pdfplumber) or upload a CSV instead.', 'danger')
            return redirect(url_for('admin.equipment'))
        try:
            pdf_bytes = file.read()
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                table_rows = None
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        table_rows = tables[0]
                        break

                if table_rows:
                    header = [ (c.strip() if c else '').lower() for c in table_rows[0] ]
                    data_rows = table_rows[1:]

                    expected = ['name', 'category', 'category_code', 'quantity']
                    use_positional = not any(re.sub(r'[^0-9a-z]+', '_', (h or '').strip().lower()) in expected for h in header)

                    def pdf_gen():
                        for r in data_rows:
                            cells = [ (c or '').strip() for c in r ]
                            if use_positional:
                                mapped = {}
                                for i, col in enumerate(expected):
                                    mapped[col] = cells[i] if i < len(cells) else ''
                                yield mapped
                            else:
                                mapped = {}
                                for i, h in enumerate(header):
                                    nk = normalize_key(h)
                                    if nk:
                                        mapped[nk] = cells[i] if i < len(cells) else ''
                                yield mapped

                    reader = pdf_gen()
                else:
                    text = '\n'.join([p.extract_text() or '' for p in pdf.pages])
                    stream = io.StringIO(text)
                    reader = csv.DictReader(stream)
        except Exception as e:
            flash('Failed to parse PDF file: ' + str(e), 'danger')
            return redirect(url_for('admin.equipment'))

    else:
        flash('Unsupported file type. Upload a CSV or PDF file.', 'danger')
        return redirect(url_for('admin.equipment'))

    # Parse rows into structured entries
    parsed_rows = []
    expected_cols = ['name', 'category', 'category_code', 'quantity']
    for idx, row in enumerate(reader, start=1):
        entry = {'row': idx, 'raw': row}

        if not isinstance(row, dict):
            # If reader yields non-dicts (e.g., pdf_gen mapped dicts, but safety)
            # attempt to coerce
            try:
                vals = list(row)
            except Exception:
                entry.update({'name': '', 'category': '', 'category_code': '', 'quantity': 0, 'valid': False, 'error': 'Could not parse row'})
                parsed_rows.append(entry)
                continue
            # map positional
            cleaned = {}
            for i, col in enumerate(expected_cols):
                cleaned[col] = vals[i] if i < len(vals) else ''
        else:
            cleaned = {}
            for k, v in row.items():
                nk = normalize_key(k)
                if not nk:
                    continue
                cleaned[nk] = (v.strip() if v is not None else '')

            if not any(k in cleaned for k in expected_cols):
                vals = [ (v or '').strip() for v in list(row.values()) ]
                for i, col in enumerate(expected_cols):
                    cleaned[col] = vals[i] if i < len(vals) else ''

        name = cleaned.get('name', '')
        category = cleaned.get('category', '')
        category_code = cleaned.get('category_code', '')
        qty_str = cleaned.get('quantity', '') or '0'

        if not category_code or not name:
            entry.update({'name': name, 'category': category, 'category_code': category_code, 'quantity': 0, 'valid': False, 'error': 'missing name or category_code'})
            parsed_rows.append(entry)
            continue

        try:
            qty = int(qty_str)
        except Exception:
            qty = 0

        entry.update({'name': name, 'category': category or '', 'category_code': category_code.upper(), 'quantity': max(0, qty), 'valid': True, 'error': ''})
        # Determine whether this will create a new item or update an existing one
        try:
            existing_db = Equipment.query.filter_by(category_code=entry['category_code'], name=entry['name']).first()
        except Exception:
            existing_db = None
        entry['action'] = 'update' if existing_db else 'create'
        if existing_db:
            entry['existing_id'] = existing_db.id
        parsed_rows.append(entry)

    action = request.form.get('action')

    # Preview flow
    if action == 'preview':
        try:
            session['equipment_upload_preview'] = json.dumps(parsed_rows)
        except Exception:
            session['equipment_upload_preview'] = str(parsed_rows)
        return render_template('equipment_upload_preview.html', rows=parsed_rows)

    # Confirm flow: prefer parsed rows from session if present
    if action == 'confirm':
        raw = session.pop('equipment_upload_preview', None)
        if raw:
            try:
                parsed_rows = json.loads(raw)
            except Exception:
                try:
                    parsed_rows = eval(raw)
                except Exception:
                    pass

    # Commit parsed rows to DB
    created = 0
    updated = 0
    skipped = 0
    errors = []

    for entry in parsed_rows:
        if not entry.get('valid'):
            skipped += 1
            errors.append(f"Row {entry.get('row')}: {entry.get('error')}")
            continue

        name = entry['name']
        category = entry.get('category', '')
        category_code = entry.get('category_code', '')
        qty = int(entry.get('quantity', 0) or 0)

        # If any equipment with the same category_code exists, update it instead of creating new
        existing_by_code = Equipment.query.filter_by(category_code=category_code).first()
        if existing_by_code:
            existing_by_code.quantity = (existing_by_code.quantity or 0) + max(0, qty)
            db.session.add(existing_by_code)
            updated += 1
        else:
            new_item = Equipment(
                name=name,
                category=category or '',
                category_code=category_code,
                quantity=max(0, qty),
                serial_number=uuid.uuid4().hex
            )
            db.session.add(new_item)
            created += 1

    try:
        db.session.commit()
        flash(f'CSV import finished. Created: {created}, Updated: {updated}, Skipped: {skipped}', 'success')
        if errors:
            flash('Some rows had issues: ' + '; '.join(errors), 'warning')
    except Exception as e:
        db.session.rollback()
        flash('Error importing CSV: ' + str(e), 'danger')

    return redirect(url_for('admin.equipment'))


@admin_bp.route('/equipment/<int:equipment_id>/toggle', methods=['POST'])
@login_required
def equipment_toggle(equipment_id):
    """Toggle equipment active state (enable/disable)."""
    eq = db.session.get(Equipment, equipment_id)
    if not eq:
        flash('Equipment not found.', 'danger')
        return redirect(url_for('admin.equipment'))

    try:
        eq.is_active = not getattr(eq, 'is_active', True)
        db.session.commit()
        flash(f'Equipment "{eq.name}" has been {"enabled" if eq.is_active else "disabled"}.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not update equipment state. Please try again.', 'danger')

    return redirect(url_for('admin.equipment'))


@admin_bp.route('/equipment/<int:equipment_id>/edit', methods=['GET', 'POST'])
@login_required
def equipment_edit(equipment_id):
    """Edit an existing equipment item."""
    # Explicit admin-only guard
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)

    eq = db.session.get(Equipment, equipment_id)
    if not eq:
        flash('Equipment not found.', 'danger')
        return redirect(url_for('admin.equipment'))

    if request.method == 'GET':
        return render_template('equipment_edit.html', equipment=eq)

    # POST: process update
    name = request.form.get('name', '').strip()
    category = request.form.get('category', '').strip()
    category_code = request.form.get('category_code', '').strip().upper()
    try:
        quantity = int(request.form.get('quantity', 0))
    except Exception:
        quantity = None

    # Basic validation
    if not name or not category_code or quantity is None or quantity < 0:
        flash('Please provide valid name, category code and non-negative quantity.', 'danger')
        return redirect(url_for('admin.equipment_edit', equipment_id=equipment_id))

    # Only enforce category_code uniqueness if it was changed
    original_code = (eq.category_code or '').strip().upper()
    if category_code != original_code:
        existing_code = Equipment.query.filter(Equipment.category_code == category_code, Equipment.id != eq.id).first()
        if existing_code:
            flash('Category code already in use by another item. Choose a different code.', 'danger')
            return redirect(url_for('admin.equipment_edit', equipment_id=equipment_id))

    # Apply updates
    eq.name = name
    eq.category = category
    eq.category_code = category_code
    eq.quantity = quantity

    # Optional fields: condition and is_active
    cond = request.form.get('condition')
    if cond:
        eq.condition = cond
    is_active = request.form.get('is_active')
    eq.is_active = True if is_active == 'on' or is_active == '1' else False

    try:
        db.session.add(eq)
        db.session.commit()
        flash('Equipment updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Could not update equipment: ' + str(e), 'danger')

    return redirect(url_for('admin.equipment'))


@admin_bp.route('/equipment/<int:equipment_id>/delete', methods=['POST'])
@login_required
def equipment_delete(equipment_id):
    """Delete an equipment item if safe to do so."""
    # Explicit admin-only guard
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)

    eq = db.session.get(Equipment, equipment_id)
    if not eq:
        flash('Equipment not found.', 'danger')
        return redirect(url_for('admin.equipment'))

    # Prevent deleting if there are any issued records referencing this equipment
    try:
        issued_count = eq.issued_items.count()
    except Exception:
        issued_count = 0

    if issued_count > 0:
        flash('Cannot delete equipment with associated issued records. Mark as disabled instead.', 'danger')
        return redirect(url_for('admin.equipment'))

    try:
        db.session.delete(eq)
        db.session.commit()
        flash('Equipment deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting equipment: ' + str(e), 'danger')

    return redirect(url_for('admin.equipment'))

@admin_bp.route('/clearance-report')
@login_required
def clearance_report():
    """Show all issued equipment for students for clearance purposes, or for staff"""
    # Explicit admin-only guard: return 403 for non-admins
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)
    # Get recipient ID filter from query string
    recipient_id = request.args.get('student_id', '').strip()  # keep student_id for backward compatibility, but treat as recipient_id

    # Base query
    query = IssuedEquipment.query

    # Apply recipient ID filter if provided
    if recipient_id:
        query = query.filter(
            db.or_(
                IssuedEquipment.student_id.ilike(f"%{recipient_id}%"),
                IssuedEquipment.staff_payroll.ilike(f"%{recipient_id}%")
            )
        )

    # Get all issued equipment (both current and returned)
    issued_items = query.order_by(IssuedEquipment.date_issued.desc()).all()

    # Check if this is for a student or staff
    is_student = any(it.student for it in issued_items)
    is_staff = any(it.staff for it in issued_items)

    # Calculate clearance status counts directly from database
    clearance_counts = {'Cleared': 0, 'Pending': 0, 'Overdue': 0, 'Total': 0}
    status_map = {}
    recipient_info = {}  # Store recipient name and type for display

    # Get unique recipient IDs (both students and staff) from the filtered results
    recipient_ids = set()
    for it in issued_items:
        if it.student_id:
            recipient_ids.add(('student', it.student_id))
        elif it.staff_payroll:
            recipient_ids.add(('staff', it.staff_payroll))

    clearance_counts['Total'] = len(recipient_ids)

    from Utils.clearance_integration import get_clearance_status
    for recipient_type, recipient_id in recipient_ids:
        status = get_clearance_status(recipient_id, recipient_type)
        status_map[recipient_id] = status
        clearance_counts[status] = clearance_counts.get(status, 0) + 1

        # Build recipient info for display, include issuing storekeeper and campus
        recipient_name = 'Unknown'
        issued_by_display = ''
        campus_name = ''

        # Get representative (most recent) issued record for this recipient
        rep_issue = IssuedEquipment.query.filter(
            db.or_(IssuedEquipment.student_id == recipient_id, IssuedEquipment.staff_payroll == recipient_id)
        ).order_by(IssuedEquipment.date_issued.desc()).first()

        if rep_issue:
            issued_by_display = rep_issue.issued_by or ''
            # Try to resolve issued_by to a StoreKeeper (payroll_number)
            sk = None
            try:
                sk = StoreKeeper.query.filter_by(payroll_number=issued_by_display).first()
            except Exception:
                sk = None
            if sk:
                issued_by_display = sk.full_name
                campus_name = sk.campus.name if sk.campus else ''

        if recipient_type == 'student':
            student = Student.query.get(recipient_id)
            if student:
                recipient_name = student.name
        else:  # staff
            staff = Staff.query.get(recipient_id)
            if staff:
                recipient_name = staff.name

        recipient_info[recipient_id] = {
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
                           is_student=is_student,
                           is_staff=is_staff)


@admin_bp.route('/clearance/<path:recipient_id>/items', methods=['GET', 'POST'])
@login_required
def clearance_manage_items(recipient_id):
    """Manage damaged/lost items for clearance: allow admin to mark items as replaced.
    
    GET: show damaged/lost returned items for the recipient.
    POST: mark items as replaced to help clear the recipient.
    """
    # Explicit admin-only guard
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)

    recipient_id = (recipient_id or '').strip()
    if not recipient_id:
        flash('Missing recipient identifier.', 'danger')
        return redirect(url_for('admin.clearance_report'))

    # Get all returned items for this recipient (both student and staff)
    all_items = IssuedEquipment.query.filter(
        IssuedEquipment.status == 'Returned',
        db.or_(
            IssuedEquipment.student_id == recipient_id,
            IssuedEquipment.staff_payroll == recipient_id
        )
    ).order_by(IssuedEquipment.date_returned.desc()).all()

    # Filter to only damaged/lost items (not marked as replaced)
    damaged_lost_items = []
    for item in all_items:
        if item.return_conditions:
            try:
                conditions = json.loads(item.return_conditions)
                # Skip if already marked as replaced
                if isinstance(conditions, dict) and conditions.get('replaced'):
                    continue
                # Check if any condition is damaged or lost
                has_damage = False
                if isinstance(conditions, dict):
                    for cond in conditions.values():
                        if isinstance(cond, str) and cond.lower() in ('damaged', 'lost'):
                            has_damage = True
                            break
                elif isinstance(conditions, str) and conditions.lower() in ('damaged', 'lost'):
                    has_damage = True
                
                if has_damage:
                    damaged_lost_items.append(item)
            except (json.JSONDecodeError, TypeError):
                pass

    # Get recipient info
    recipient_name = 'Unknown'
    recipient_type = 'Student'
    student = Student.query.get(recipient_id)
    if student:
        recipient_name = student.name
        recipient_type = 'Student'
    else:
        staff = Staff.query.get(recipient_id)
        if staff:
            recipient_name = staff.name
            recipient_type = 'Staff'

    if request.method == 'GET':
        return render_template('clearance_manage_items.html', 
                             recipient_id=recipient_id, 
                             recipient_name=recipient_name,
                             recipient_type=recipient_type,
                             items=damaged_lost_items)

    # POST: apply actions to items
    processed_items = []
    action_counts = {'replaced': 0, 'repaired': 0, 'waiver': 0}
    
    for item in damaged_lost_items:
        action_key = f'action_{item.id}'
        action = request.form.get(action_key, '').strip()
        
        if not action:
            continue
        
        if action not in ('replaced', 'repaired', 'waiver'):
            continue
        
        try:
            equipment = db.session.get(Equipment, item.equipment_id)
        except Exception:
            equipment = None
        
        # For 'replaced' action: adjust equipment counts (reverse damaged/lost increments)
        # For 'repaired' and 'waiver': keep inventory as is (no adjustment needed)
        if action == 'replaced' and equipment:
            conditions = json.loads(item.return_conditions or '{}')
            for cond in conditions.values():
                if isinstance(cond, str) and cond.lower() == 'damaged':
                    equipment.damaged_count = max(0, (equipment.damaged_count or 0) - 1)
                    equipment.quantity = (equipment.quantity or 0) + 1
                elif isinstance(cond, str) and cond.lower() == 'lost':
                    equipment.lost_count = max(0, (equipment.lost_count or 0) - 1)
                    equipment.quantity = (equipment.quantity or 0) + 1
            db.session.add(equipment)
        
        # Store the action taken in return_conditions
        item.return_conditions = json.dumps({
            'action': action,
            'action_date': datetime.now(UTC).isoformat(),
            'action_by': current_user.username if current_user else 'System'
        })
        db.session.add(item)
        processed_items.append(str(item.id))
        action_counts[action] += 1

    if processed_items:
        try:
            db.session.commit()
            message_parts = []
            if action_counts['replaced'] > 0:
                message_parts.append(f"{action_counts['replaced']} replaced")
            if action_counts['repaired'] > 0:
                message_parts.append(f"{action_counts['repaired']} repaired")
            if action_counts['waiver'] > 0:
                message_parts.append(f"{action_counts['waiver']} waiver")
            
            flash(f'Actions applied: {", ".join(message_parts)}. Clearance status updated.', 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error applying actions: ' + str(e), 'danger')
        return redirect(url_for('admin.clearance_report'))
    else:
        # No items were processed
        if damaged_lost_items:
            flash('Please select items and choose actions.', 'warning')
        else:
            flash('No damaged/lost items found for this recipient.', 'info')
        return redirect(url_for('admin.clearance_manage_items', recipient_id=recipient_id))


@admin_bp.route('/clearance/<path:student_id>/manage', methods=['GET', 'POST'])
@login_required
def clearance_manage(student_id):
    """Manage clearance for a specific student: allow admin to attempt to clear.

    GET: show issued items and their return conditions.
    POST: evaluate items and set Clearance.status to 'Cleared' or 'Pending'.
    """
    # Explicit admin-only guard
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)

    student_id = (student_id or '').strip()
    if not student_id:
        flash('Missing student identifier.', 'danger')
        return redirect(url_for('admin.clearance_report'))

    items = IssuedEquipment.query.filter(IssuedEquipment.student_id == student_id).order_by(IssuedEquipment.date_issued.desc()).all()

    if request.method == 'GET':
        return render_template('clearance_manage.html', student_id=student_id, items=items)

    # POST: attempt to clear
    # First, handle any replacements submitted for damaged/lost items
    replaced_ids = []
    for it in items:
        form_key = f'replaced_{it.id}'
        if request.form.get(form_key):
            try:
                equipment = db.session.get(Equipment, it.equipment_id)
            except Exception:
                equipment = None
            # Adjust equipment counts: reverse damaged/lost increments and add back to quantity
            if equipment:
                conditions = json.loads(it.return_conditions or '{}')
                for cond in conditions.values():
                    if cond.lower() == 'damaged':
                        equipment.damaged_count = max(0, (equipment.damaged_count or 0) - 1)
                        equipment.quantity = (equipment.quantity or 0) + 1
                    elif cond.lower() == 'lost':
                        equipment.lost_count = max(0, (equipment.lost_count or 0) - 1)
                        equipment.quantity = (equipment.quantity or 0) + 1
                db.session.add(equipment)
            # Mark the issue's return condition as Replaced
            it.return_conditions = json.dumps({'replaced': True})
            db.session.add(it)
            replaced_ids.append(str(it.id))

    if replaced_ids:
        try:
            db.session.commit()
            flash('Marked replaced for items: ' + ', '.join(replaced_ids), 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error recording replacements: ' + str(e), 'danger')

    # If there are no items, mark as Cleared
    clearance = Clearance.query.filter_by(student_id=student_id).first()
    if not clearance:
        clearance = Clearance(student_id=student_id)
        db.session.add(clearance)

    if not items:
        clearance.status = 'Cleared'
        clearance.last_updated = datetime.now(UTC)
        db.session.commit()
        flash('No issued items found. Student marked as Cleared.', 'success')
        return redirect(url_for('admin.clearance_report', student_id=student_id))

    # Check for outstanding issued items
    outstanding = [it for it in items if it.status != 'Returned']
    if outstanding:
        clearance.status = 'Pending'
        clearance.last_updated = datetime.now(UTC)
        db.session.commit()
        flash('Student has outstanding issued items and cannot be cleared.', 'danger')
        return redirect(url_for('admin.clearance_report', student_id=student_id))

    # All items are returned - check their return conditions
    bad = [it for it in items if any(c.lower() in ('damaged', 'lost') for c in json.loads(it.return_conditions or '{}').values())]
    if bad:
        clearance.status = 'Pending'
        clearance.last_updated = datetime.now(UTC)
        db.session.commit()
        flash('Some returned items are Damaged or Lost. Clearance remains Pending/Uncleared.', 'warning')
        return redirect(url_for('admin.clearance_report', student_id=student_id))

    # All returned and all Good
    clearance.status = 'Cleared'
    clearance.last_updated = datetime.now(UTC)
    db.session.commit()
    flash('Student successfully cleared.', 'success')
    return redirect(url_for('admin.clearance_report', student_id=student_id))


@admin_bp.route('/clearance/staff/<path:staff_payroll>/manage', methods=['GET', 'POST'])
@login_required
def clearance_manage_staff(staff_payroll):
    """Manage clearance for a specific staff member: allow admin to attempt to clear.

    GET: show issued items and their return conditions.
    POST: evaluate items and set clearance status.
    """
    # Explicit admin-only guard
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)

    staff_payroll = (staff_payroll or '').strip()
    if not staff_payroll:
        flash('Missing staff payroll number.', 'danger')
        return redirect(url_for('admin.clearance_report'))

    items = IssuedEquipment.query.filter(IssuedEquipment.staff_payroll == staff_payroll).order_by(IssuedEquipment.date_issued.desc()).all()

    if request.method == 'GET':
        return render_template('clearance_manage_staff.html', staff_payroll=staff_payroll, items=items)

    # POST: attempt to clear
    # First, handle any replacements submitted for damaged/lost items
    replaced_ids = []
    for it in items:
        form_key = f'replaced_{it.id}'
        if request.form.get(form_key):
            try:
                equipment = db.session.get(Equipment, it.equipment_id)
            except Exception:
                equipment = None
            # Adjust equipment counts: reverse damaged/lost increments and add back to quantity
            if equipment:
                conditions = json.loads(it.return_conditions or '{}')
                for cond in conditions.values():
                    if cond.lower() == 'damaged':
                        equipment.damaged_count = max(0, (equipment.damaged_count or 0) - 1)
                        equipment.quantity = (equipment.quantity or 0) + 1
                    elif cond.lower() == 'lost':
                        equipment.lost_count = max(0, (equipment.lost_count or 0) - 1)
                        equipment.quantity = (equipment.quantity or 0) + 1
                db.session.add(equipment)
            # Mark the issue's return condition as Replaced
            it.return_conditions = json.dumps({'replaced': True})
            db.session.add(it)
            replaced_ids.append(str(it.id))

    if replaced_ids:
        try:
            db.session.commit()
            flash('Marked replaced for items: ' + ', '.join(replaced_ids), 'success')
        except Exception as e:
            db.session.rollback()
            flash('Error recording replacements: ' + str(e), 'danger')

    # For staff, we don't store clearance status in the Clearance table
    # (it's designed for students), so we just validate the criteria
    if not items:
        flash('No issued items found. Staff member is cleared.', 'success')
        return redirect(url_for('admin.clearance_report', student_id=staff_payroll))

    # Check for outstanding issued items
    outstanding = [it for it in items if it.status != 'Returned']
    if outstanding:
        flash('Staff member has outstanding issued items and cannot be cleared.', 'danger')
        return redirect(url_for('admin.clearance_report', student_id=staff_payroll))

    # All items are returned - check their return conditions
    bad = [it for it in items if any(c.lower() in ('damaged', 'lost') for c in json.loads(it.return_conditions or '{}').values())]
    if bad:
        flash('Some returned items are Damaged or Lost. Clearance remains Pending.', 'warning')
        return redirect(url_for('admin.clearance_report', student_id=staff_payroll))

    # All returned and all Good
    flash('Staff member successfully cleared.', 'success')
    return redirect(url_for('admin.clearance_report', student_id=staff_payroll))


@admin_bp.route('/clearance-report/print')
@login_required
def clearance_report_print():
    """Printable view of the clearance report that auto-triggers browser print (user can Save as PDF)."""
    # Explicit admin-only guard: return 403 for non-admins
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)
    recipient_id = request.args.get('student_id', '').strip()

    query = IssuedEquipment.query
    if recipient_id:
        query = query.filter(
            db.or_(
                IssuedEquipment.student_id.ilike(f"%{recipient_id}%"),
                IssuedEquipment.staff_payroll.ilike(f"%{recipient_id}%")
            )
        )

    issued_items = query.order_by(IssuedEquipment.date_issued.desc()).all()
    # Derive recipient name from the returned items when available
    recipient_name = ''
    if issued_items:
        # Use the first matched item's recipient_name as representative
        first_item = issued_items[0]
        if first_item.student:
            recipient_name = first_item.student.name
        elif first_item.staff:
            recipient_name = first_item.staff.name

    # Categorize items for the print template
    not_returned_items = []
    damaged_items = []
    lost_items = []
    cleared_items = []

    for item in issued_items:
        if item.status != 'Returned':
            not_returned_items.append(item)
        elif item.return_condition == 'Damaged':
            damaged_items.append(item)
        elif item.return_condition == 'Lost':
            lost_items.append(item)
        elif item.return_condition == 'Good':
            cleared_items.append(item)

    return render_template('clearance_report_print.html',
                           issued_items=issued_items,
                           not_returned_items=not_returned_items,
                           damaged_items=damaged_items,
                           lost_items=lost_items,
                           cleared_items=cleared_items,
                           student_id=recipient_id,
                           student_name=recipient_name,
                           generated_on=datetime.now())

@admin_bp.route('/clearance-report/export')
@login_required
def clearance_report_export():
    """Export clearance report to CSV."""
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)
    recipient_id = request.args.get('student_id', '').strip()

    query = IssuedEquipment.query
    if recipient_id:
        query = query.filter(
            db.or_(
                IssuedEquipment.student_id.ilike(f"%{recipient_id}%"),
                IssuedEquipment.staff_payroll.ilike(f"%{recipient_id}%")
            )
        )

    issued_items = query.order_by(IssuedEquipment.date_issued.desc()).all()

    # Create CSV
    import csv
    from io import StringIO
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Recipient ID', 'Recipient Name', 'Equipment Name', 'Category', 'Quantity', 'Date Issued', 'Status', 'Return Condition', 'Date Returned'])
    for item in issued_items:
        recipient_id = item.staff_payroll or item.student_id
        recipient_name = ''
        if item.student:
            recipient_name = item.student.name
        elif item.staff:
            recipient_name = item.staff.name
        writer.writerow([
            recipient_id,
            recipient_name,
            item.equipment.name if item.equipment else item.equipment_id,
            item.equipment.category if item.equipment else '',
            item.quantity,
            item.date_issued.strftime('%Y-%m-%d') if item.date_issued else '',
            item.status,
            item.return_condition or '',
            item.date_returned.strftime('%Y-%m-%d') if item.date_returned else ''
        ])
    output = si.getvalue()
    si.close()
    from flask import Response
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=clearance_report.csv"})

@admin_bp.route('/clearance-due-details/<recipient_id>')
@login_required
def clearance_due_details(recipient_id):
    """Show due equipment details for a specific recipient (student or staff) in card format."""
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)
    
    # Get due items for this recipient (could be student or staff)
    today = datetime.now().date()
    due_items = IssuedEquipment.query.filter(
        db.or_(
            IssuedEquipment.student_id == recipient_id,
            IssuedEquipment.staff_payroll == recipient_id
        ),
        IssuedEquipment.status == 'Issued',
        IssuedEquipment.expected_return != None,
        func.date(IssuedEquipment.expected_return) <= today
    ).order_by(IssuedEquipment.expected_return.asc()).all()
    
    # Determine recipient type and name
    recipient_name = ''
    recipient_type = ''
    if due_items:
        first_item = due_items[0]
        if first_item.student:
            recipient_name = first_item.student.name
            recipient_type = 'Student'
        elif first_item.staff:
            recipient_name = first_item.staff.name
            recipient_type = 'Staff'
    
    # Get issuer info
    issuer_info = {}
    for item in due_items:
        if item.issued_by:
            admin = Admin.query.filter_by(username=item.issued_by).first()
            if admin:
                issuer_info[item.id] = {'name': admin.username, 'email': admin.email, 'id': admin.id}
            else:
                storekeeper = StoreKeeper.query.filter_by(payroll_number=item.issued_by).first()
                if storekeeper:
                    issuer_info[item.id] = {'name': storekeeper.full_name, 'email': storekeeper.email, 'id': storekeeper.id}
                else:
                    issuer_info[item.id] = {'name': item.issued_by, 'email': '—', 'id': '—'}
        else:
            issuer_info[item.id] = {'name': '—', 'email': '—', 'id': '—'}
    
    return render_template('clearance_due_details.html', due_items=due_items, recipient_id=recipient_id, recipient_name=recipient_name, recipient_type=recipient_type, issuer_info=issuer_info, today=datetime.now().date())

@admin_bp.route('/issue', methods=['GET', 'POST'])
@login_required
def issue():
    # GET: render the issue form and list of issued items
    if request.method == 'GET':
        equipment = Equipment.query.filter_by(is_active=True).order_by(Equipment.name).all()
        issued = IssuedEquipment.query.order_by(IssuedEquipment.date_issued.desc()).all()
        return render_template('issue.html', equipment=equipment, issued=issued)

    person_type = request.form.get('person_type')
    # Student fields
    student_id = request.form.get('student_id')
    student_name = request.form.get('student_name')
    student_email = request.form.get('student_email')
    student_phone = request.form.get('student_phone')
    # Staff fields
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
                return redirect(url_for('admin.issue'))

    # Validation
    if person_type == 'student':
        if not student_id or not student_name or not student_email or not student_phone:
            flash('Missing required student fields.', 'danger')
            return redirect(url_for('admin.issue'))
        if '@' not in student_email or '.' not in student_email:
            flash('Invalid student email address.', 'danger')
            return redirect(url_for('admin.issue'))
        import re
        if not re.fullmatch(r'0\d{9}', student_phone or ''):
            flash('Invalid phone number. Expected format: 0712345678', 'danger')
            return redirect(url_for('admin.issue'))
        from Utils.student_checks import has_unreturned_items
        has_unreturned, unreturned_items = has_unreturned_items(student_id)
        if has_unreturned:
            items_list = ", ".join([
                f"{item.equipment.name} (Due: {item.expected_return.strftime('%Y-%m-%d') if item.expected_return else 'No due date'})"
                for item in unreturned_items
            ])
            flash(f'Student has unreturned items: {items_list}. Please return these items first.', 'danger')
            return redirect(url_for('admin.issue'))
    elif person_type == 'staff':
        if not staff_payroll or not staff_name or not staff_email:
            flash('Missing required staff fields.', 'danger')
            return redirect(url_for('admin.issue'))
        if '@' not in staff_email or '.' not in staff_email:
            flash('Invalid staff email address.', 'danger')
            return redirect(url_for('admin.issue'))
    else:
        flash('Please select who to issue to.', 'danger')
        return redirect(url_for('admin.issue'))

    if not equipment_id:
        flash('Equipment selection required.', 'danger')
        return redirect(url_for('admin.issue'))
    if not expected_return_str:
        flash('Expected return date is required.', 'danger')
        return redirect(url_for('admin.issue'))
    try:
        eq = db.session.get(Equipment, int(equipment_id))
    except Exception:
        eq = None
    if not eq:
        flash('Selected equipment not found.', 'danger')
        return redirect(url_for('admin.issue'))
    if eq.quantity < qty:
        flash(f'Not enough items available. Available: {eq.quantity}', 'danger')
        return redirect(url_for('admin.issue'))
    try:
        expected_return = datetime.strptime(expected_return_str, '%Y-%m-%d')
    except ValueError:
        flash('Invalid expected return date format.', 'danger')
        return redirect(url_for('admin.issue'))
    today_date = datetime.now().date()
    if expected_return.date() < today_date:
        flash('Expected return date cannot be in the past. Please select today or a future date.', 'danger')
        return redirect(url_for('admin.issue'))
    # Create the issued equipment record
    # First, ensure Student or Staff record exists
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
            # Update existing student info if changed
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
    else:  # staff
        staff = Staff.query.filter_by(payroll_number=staff_payroll).first()
        if not staff:
            staff = Staff(
                payroll_number=staff_payroll,
                name=staff_name,
                email=staff_email
            )
            db.session.add(staff)
        else:
            # Update existing staff info if changed
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
    # record which user performed the issuance
    try:
        issue.issued_by = current_user.username
    except Exception:
        issue.issued_by = None
    db.session.add(issue)
    eq.quantity = eq.quantity - qty
    db.session.commit()
    flash('Equipment issued successfully.', 'success')
    return redirect(url_for('admin.issue'))

@admin_bp.route('/return/<int:issue_id>', methods=['GET', 'POST'])
@login_required
def return_item(issue_id):
    """Handle equipment return with condition tracking.
    GET: Show return form with condition selection
    POST: Process return and update equipment counts based on condition
    """
    issue = IssuedEquipment.query.get_or_404(issue_id)
    
    # If already returned, redirect with message
    if issue.status == 'Returned':
        flash('This item has already been returned.', 'warning')
        return redirect(url_for('admin.issued_equipment'))

    # Parse serial numbers
    serials = []
    if issue.serial_numbers:
        try:
            serials = json.loads(issue.serial_numbers)
        except:
            serials = []

    if request.method == 'GET':
        return render_template('return_form.html', issue=issue, serials=serials)

    # Handle POST - process return
    returned_serials = request.form.getlist('returned_serials')
    
    # Validate serial numbers if present
    if serials:
        if set(returned_serials) != set(serials):
            flash('Please check all serial numbers of the items being returned.', 'danger')
            return redirect(url_for('admin.return_item', issue_id=issue_id))
        
        # Collect conditions per serial
        conditions = {}
        for serial in returned_serials:
            condition = request.form.get(f'condition_{serial}')
            if not condition or condition not in ('Good', 'Damaged', 'Lost'):
                flash(f'Please select a valid return condition for serial number {serial}.', 'danger')
                return redirect(url_for('admin.return_item', issue_id=issue_id))
            conditions[serial] = condition
    else:
        # For non-serial items, use single condition
        condition = request.form.get('condition')
        if not condition or condition not in ('Good', 'Damaged', 'Lost'):
            flash('Please select a valid return condition.', 'danger')
            return redirect(url_for('admin.return_item', issue_id=issue_id))
        conditions = condition  # For backward compatibility, but since we changed to JSON, perhaps always JSON

    # Get associated equipment record
    equipment = Equipment.query.get_or_404(issue.equipment_id)
    
    # Update issue record
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
        flash(f'Item returned successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error processing return. Please try again.', 'danger')
        return redirect(url_for('admin.return_item', issue_id=issue_id))

    return redirect(url_for('admin.issued_equipment'))


@admin_bp.route('/issued-equipment')
@login_required
def issued_equipment():
    # Group issued equipment by recipient to eliminate redundancy
    from collections import defaultdict
    from datetime import datetime

    # Get all issued equipment
    all_issued = IssuedEquipment.query.order_by(IssuedEquipment.date_issued.desc()).all()

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

    # Fetch campus distributions
    distributions = CampusDistribution.query.order_by(CampusDistribution.date_distributed.desc()).all()

    return render_template('issued_equipment.html', issued=aggregated_issued, distributions=distributions)


@admin_bp.route('/api/recipient-autocomplete')
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
        Student.name.label('name'),
        db.literal('Student').label('type')
    ).join(Student, IssuedEquipment.student_id == Student.id).filter(
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




@admin_bp.route('/reports')
@login_required
def reports():
    total_equipment = Equipment.query.count()
    issued_count = IssuedEquipment.query.filter_by(status='Issued').count()
    returned_count = IssuedEquipment.query.filter_by(status='Returned').count()
    cleared_students = Clearance.query.filter_by(status='Cleared').count()
    received_equipment_count = CampusDistribution.query.count()

    return render_template(
        'reports.html',
        total_equipment=total_equipment,
        issued_count=issued_count,
        returned_count=returned_count,
        cleared_students=cleared_students,
        received_equipment_count=received_equipment_count
    )

@admin_bp.route('/issued_report')
@login_required
def issued_report():
    # Allow filtering by equipment via query string: ?equipment_id=<id>&page=1&per_page=25&export=csv|excel
    equipment_id = request.args.get('equipment_id', 'All')
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get('per_page', 25))
    except ValueError:
        per_page = 25
    export = request.args.get('export')

    equipments = Equipment.query.order_by(Equipment.name).all()

    base_q = IssuedEquipment.query.filter_by(status='Issued')
    if equipment_id and equipment_id != 'All':
        try:
            eq_id = int(equipment_id)
            base_q = base_q.filter_by(equipment_id=eq_id)
        except ValueError:
            pass

    total = base_q.count()
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1

    # Export unpaginated full filtered results
    if export in ('csv', 'excel'):
        items = base_q.order_by(IssuedEquipment.date_issued.desc()).all()
        issuer_info = {}
        for item in items:
            if item.issued_by:
                admin = Admin.query.filter_by(username=item.issued_by).first()
                if admin:
                    issuer_info[item.id] = {'name': admin.username, 'email': admin.email, 'id': admin.id}
                else:
                    storekeeper = StoreKeeper.query.filter_by(payroll_number=item.issued_by).first()
                    if storekeeper:
                        issuer_info[item.id] = {'name': storekeeper.full_name, 'email': storekeeper.email, 'id': storekeeper.id}
                    else:
                        issuer_info[item.id] = {'name': item.issued_by, 'email': '—', 'id': '—'}
            else:
                issuer_info[item.id] = {'name': '—', 'email': '—', 'id': '—'}
        # Build CSV
        import csv
        from io import StringIO
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['Recipient ID', 'Recipient Name', 'Email', 'Phone', 'Equipment Name', 'Category', 'Quantity', 'Date Issued', 'Issuer Name', 'Issuer Email', 'Issuer ID'])
        for issue in items:
            recipient_id = issue.staff_payroll or issue.student_id
            recipient_name = ''
            recipient_email = ''
            recipient_phone = ''
            if issue.student:
                recipient_name = issue.student.name
                recipient_email = issue.student.email
                recipient_phone = issue.student.phone
            elif issue.staff:
                recipient_name = issue.staff.name
                recipient_email = issue.staff.email
            writer.writerow([
                recipient_id,
                recipient_name,
                recipient_email or '—',
                recipient_phone or '—',
                issue.equipment.name if issue.equipment else issue.equipment_id,
                issue.equipment.category if issue.equipment else '',
                issue.quantity,
                issue.date_issued.strftime('%Y-%m-%d'),
                issuer_info[issue.id]['name'],
                issuer_info[issue.id]['email'],
                issuer_info[issue.id]['id']
            ])
        output = si.getvalue()
        si.close()
        from flask import Response
        if export == 'csv':
            mimetype = 'text/csv'
            fname = 'issued_items.csv'
        else:
            mimetype = 'application/vnd.ms-excel'
            fname = 'issued_items.xls'
        return Response(output, mimetype=mimetype, headers={"Content-Disposition": f"attachment;filename={fname}"})

    items = base_q.order_by(IssuedEquipment.date_issued.desc()).offset((page-1)*per_page).limit(per_page).all()

    issuer_info = {}
    for item in items:
        if item.issued_by:
            admin = Admin.query.filter_by(username=item.issued_by).first()
            if admin:
                issuer_info[item.id] = {'name': admin.username, 'email': admin.email, 'id': admin.id}
            else:
                storekeeper = StoreKeeper.query.filter_by(payroll_number=item.issued_by).first()
                if storekeeper:
                    issuer_info[item.id] = {'name': storekeeper.full_name, 'email': storekeeper.email, 'id': storekeeper.id}
                else:
                    issuer_info[item.id] = {'name': item.issued_by, 'email': '—', 'id': '—'}
        else:
            issuer_info[item.id] = {'name': '—', 'email': '—', 'id': '—'}

    return render_template('issued_report.html', issued_items=items, equipments=equipments, selected_equipment=equipment_id, page=page, per_page=per_page, total=total, total_pages=total_pages, issuer_info=issuer_info)

@admin_bp.route('/api/inventory_top')
@login_required
def api_inventory_top():
    """Return top-N equipment with available/issued/damaged/lost counts as JSON."""
    try:
        top = int(request.args.get('top', 10))
    except ValueError:
        top = 10
    name = request.args.get('name', '').strip()

    q = Equipment.query
    if name:
        q = q.filter(Equipment.name.ilike(f"%{name}%"))

    items = q.order_by(Equipment.quantity.desc()).limit(top).all()

    labels = [f"{i.name} ({i.category_code})" for i in items]
    available = [i.available_quantity for i in items]
    issued = [i.issued_items.filter_by(status='Issued').count() for i in items]
    damaged = [i.damaged_count for i in items]
    lost = [i.lost_count for i in items]

    return jsonify(labels=labels, available=available, issued=issued, damaged=damaged, lost=lost)


@admin_bp.route('/api/return_conditions')
@login_required
def api_return_conditions():
    """Return counts of returned items grouped by return_condition."""
    rows = db.session.query(IssuedEquipment.return_condition, func.count(IssuedEquipment.id)).\
        filter(IssuedEquipment.status == 'Returned').group_by(IssuedEquipment.return_condition).all()

    labels = []
    data = []
    for cond, cnt in rows:
        labels.append(cond or 'Unknown')
        data.append(cnt)

    return jsonify(labels=labels, data=data)


@admin_bp.route('/api/issues_timeseries')
@login_required
def api_issues_timeseries():
    """Return issued and returned counts per day for the past N days (default 30)."""
    try:
        days = int(request.args.get('days', 30))
    except ValueError:
        days = 30

    end = datetime.utcnow()
    start = end - timedelta(days=days-1)

    # Issued per day
    issued_rows = db.session.query(func.date(IssuedEquipment.date_issued), func.count(IssuedEquipment.id)).\
        filter(IssuedEquipment.date_issued >= start).group_by(func.date(IssuedEquipment.date_issued)).\
        order_by(func.date(IssuedEquipment.date_issued)).all()

    returned_rows = db.session.query(func.date(IssuedEquipment.date_returned), func.count(IssuedEquipment.id)).\
        filter(IssuedEquipment.date_returned != None).filter(IssuedEquipment.date_returned >= start).\
        group_by(func.date(IssuedEquipment.date_returned)).order_by(func.date(IssuedEquipment.date_returned)).all()

    issued_map = {str(r[0]): r[1] for r in issued_rows}
    returned_map = {str(r[0]): r[1] for r in returned_rows}

    labels = []
    issued_data = []
    returned_data = []
    for i in range(days):
        d = (start + timedelta(days=i)).date()
        key = str(d)
        labels.append(d.strftime('%Y-%m-%d'))
        issued_data.append(issued_map.get(key, 0))
        returned_data.append(returned_map.get(key, 0))

    return jsonify(labels=labels, issued=issued_data, returned=returned_data)

@admin_bp.route('/equipment-report')
@login_required
def equipment_report():
    search_name = request.args.get('name', '').strip()
    export_format = request.args.get('export')

    # Base query
    base_q = Equipment.query

    # Apply name or category code filter if provided (case-insensitive, partial match)
    if search_name:
        base_q = base_q.filter(
            db.or_(
                Equipment.name.ilike(f"%{search_name}%"),
                Equipment.category_code.ilike(f"%{search_name}%")
            )
        )

    # Fetch all results (unpaginated)
    equipments = base_q.order_by(Equipment.category, Equipment.name).all()

    # Handle export
    if export_format:
        output = io.StringIO()
        writer = csv.writer(output)
        # Write headers
        writer.writerow(['Category Name', 'Equipment Name', 'Category Code', 'Total Quantity', 'Available', 'Issued', 'Damaged', 'Lost'])
        
        # Group equipment by category
        from itertools import groupby
        for category, group in groupby(equipments, key=lambda x: x.category):
            group_list = list(group)
            for index, item in enumerate(group_list):
                # Only write category name for the first item in each group
                if index == 0:
                    writer.writerow([
                        item.category,
                        item.name,
                        item.category_code,
                        item.quantity,
                        item.available_quantity,
                        item.issued_items.filter_by(status='Issued').count(),
                        item.damaged_count,
                        item.lost_count,
                    ])
                else:
                    # For subsequent items in the group, leave category name blank
                    writer.writerow([
                        '',
                        item.name,
                        item.category_code,
                        item.quantity,
                        item.available_quantity,
                        item.issued_items.filter_by(status='Issued').count(),
                        item.damaged_count,
                        item.lost_count,
                    ])
        output.seek(0)
        if export_format == 'csv':
            mimetype = 'text/csv'
            fname = 'equipment_inventory.csv'
        else:
            mimetype = 'application/vnd.ms-excel'
            fname = 'equipment_inventory.xls'
        return Response(output.getvalue(), mimetype=mimetype, headers={"Content-Disposition": f"attachment;filename={fname}"})

    # Calculate issued count for each equipment
    for equipment in equipments:
        equipment.issued_count = equipment.issued_items.filter_by(status='Issued').count()

    return render_template('equipment_report.html',
                         equipments=equipments,
                         search_name=search_name)


@admin_bp.route('/distribute-to-campus', methods=['GET', 'POST'])
@login_required
def distribute_to_campus():
    """Distribute equipment to satellite campuses.
    
    GET: Show distribution form with satellite campuses and equipment dropdown
    POST: Submit distribution and record it
    """
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)
    
    if request.method == 'GET':
        campuses = SatelliteCampus.query.filter_by(is_active=True).all()
        return render_template('distribute_to_campus.html', campuses=campuses)
    
    # POST: Process distribution
    campus_id = request.form.get('campus_id', '').strip()
    category_code = request.form.get('category_code', '').strip()
    category_name = request.form.get('category_name', '').strip()
    equipment_id = request.form.get('equipment_id', '').strip()
    quantity_str = request.form.get('quantity', '').strip()
    notes = request.form.get('notes', '').strip()
    document = request.files.get('document')
    
    # Validate inputs
    if not all([campus_id, category_code, category_name, equipment_id, quantity_str]):
        flash('Please fill in all fields.', 'danger')
        return redirect(url_for('admin.distribute_to_campus'))
    
    try:
        campus_id = int(campus_id)
        equipment_id = int(equipment_id)
        quantity = int(quantity_str)
        if quantity <= 0:
            raise ValueError('Quantity must be positive')
    except (ValueError, TypeError):
        flash('Invalid input: ensure campus, equipment, and quantity are correct.', 'danger')
        return redirect(url_for('admin.distribute_to_campus'))
    
    # Verify campus exists
    campus = SatelliteCampus.query.get(campus_id)
    if not campus or not campus.is_active:
        flash('Invalid satellite campus selected.', 'danger')
        return redirect(url_for('admin.distribute_to_campus'))
    
    # Verify equipment exists and has sufficient quantity
    equipment = Equipment.query.get(equipment_id)
    if not equipment or not equipment.is_active:
        flash('Invalid equipment selected.', 'danger')
        return redirect(url_for('admin.distribute_to_campus'))
    
    if equipment.quantity < quantity:
        flash(f'Insufficient quantity. Available: {equipment.quantity}, Requested: {quantity}', 'danger')
        return redirect(url_for('admin.distribute_to_campus'))
    
    # Handle file upload if provided
    document_path = None
    if document and document.filename:
        try:
            from werkzeug.utils import secure_filename
            import os
            
            # Create documents directory if it doesn't exist
            upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads', 'distributions')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Validate file extension
            allowed_extensions = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png'}
            if '.' in document.filename:
                ext = document.filename.rsplit('.', 1)[1].lower()
                if ext not in allowed_extensions:
                    flash('Invalid file format. Allowed: PDF, DOC, DOCX, XLS, XLSX, JPG, JPEG, PNG', 'warning')
                else:
                    # Save file with timestamp
                    from datetime import datetime
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"dist_{campus_id}_{equipment_id}_{timestamp}_{secure_filename(document.filename)}"
                    document.save(os.path.join(upload_dir, filename))
                    document_path = f"distributions/{filename}"
        except Exception as e:
            flash(f'Warning: Could not save document - {str(e)}', 'warning')
    
    try:
        # Create distribution record
        distribution = CampusDistribution(
            campus_id=campus_id,
            equipment_id=equipment_id,
            category_code=category_code,
            category_name=category_name,
            quantity=quantity,
            distributed_by=current_user.username,
            notes=notes if notes else None,
            document_path=document_path
        )
        db.session.add(distribution)
        
        # Update equipment quantity
        equipment.quantity -= quantity
        db.session.add(equipment)
        
        db.session.commit()
        flash(f'Successfully distributed {quantity} units of {equipment.name} to {campus.name}.', 'success')
        if document_path:
            flash('Supporting document uploaded successfully.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error during distribution: {str(e)}', 'danger')
    
    return redirect(url_for('admin.distribute_to_campus'))


@admin_bp.route('/manage-campuses', methods=['GET', 'POST'])
@login_required
def manage_campuses():
    """Simple campus management: list and add satellite campuses."""
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        location = request.form.get('location', '').strip()
        if not name or not code:
            flash('Campus name and code are required.', 'danger')
            return redirect(url_for('admin.manage_campuses'))

        existing = SatelliteCampus.query.filter((SatelliteCampus.name == name) | (SatelliteCampus.code == code)).first()
        if existing:
            flash('Campus with that name or code already exists.', 'warning')
            return redirect(url_for('admin.manage_campuses'))

        campus = SatelliteCampus(name=name, code=code, location=location, is_active=True)
        db.session.add(campus)
        db.session.commit()
        flash('Satellite campus added.', 'success')
        return redirect(url_for('admin.manage_campuses'))

    campuses = SatelliteCampus.query.order_by(SatelliteCampus.name).all()
    return render_template('manage_campuses.html', campuses=campuses)


@admin_bp.route('/distributions')
@login_required
def view_distributions():
    """View all campus distributions with download capability for uploaded documents."""
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)
    
    distributions = CampusDistribution.query.order_by(CampusDistribution.date_distributed.desc()).all()
    return render_template('distributions.html', distributions=distributions)


@admin_bp.route('/api/categories')
@login_required
def api_categories():
    """API endpoint to get all equipment categories."""
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)
    
    categories = EquipmentCategory.query.filter_by(is_active=True).all()
    return jsonify([
        {'id': cat.id, 'code': cat.category_code, 'name': cat.category_name}
        for cat in categories
    ])


@admin_bp.route('/api/equipment-by-category/<category_code>')
@login_required
def api_equipment_by_category(category_code):
    """API endpoint to get equipment items matching a category code."""
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)
    
    equipment_list = Equipment.query.filter_by(
        category_code=category_code,
        is_active=True
    ).all()
    return jsonify([
        {'id': eq.id, 'name': eq.name, 'quantity': eq.quantity}
        for eq in equipment_list
    ])


@admin_bp.route('/download-distribution-document/<int:distribution_id>')
@login_required
def download_distribution_document(distribution_id):
    """Download supporting document for a distribution."""
    if not (current_user.is_authenticated and isinstance(current_user, Admin)):
        abort(403)
    
    distribution = CampusDistribution.query.get_or_404(distribution_id)
    
    if not distribution.document_path:
        flash('No document available for this distribution.', 'warning')
        return redirect(url_for('admin.issued_equipment'))
    
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
        return redirect(url_for('admin.issued_equipment'))
    
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
        return redirect(url_for('admin.issued_equipment'))

@admin_bp.route('/profile', methods=['POST'])
@login_required
def profile():
    """Update admin profile (email)"""
    if not isinstance(current_user, Admin):
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    try:
        data = request.get_json()
        email = data.get('email', '').strip() if data else None
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'})
        
        # Validate email format
        if '@' not in email or '.' not in email:
            return jsonify({'success': False, 'error': 'Invalid email format'})
        
        # Check if email already exists for another admin
        existing = Admin.query.filter(Admin.id != current_user.id, Admin.email == email).first()
        if existing:
            return jsonify({'success': False, 'error': 'Email already in use'})
        
        current_user.email = email
        db.session.commit()
        return jsonify({'success': True, 'message': 'Profile updated'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change admin password"""
    if not isinstance(current_user, Admin):
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


@admin_bp.route('/user-management')
@login_required
def user_management():
    """View all storekeepers and their approval status"""
    # Get all pending (unapproved) storekeepers
    pending_storekeepers = StoreKeeper.query.filter_by(is_approved=False).all()
    
    # Get all approved storekeepers
    approved_storekeepers = StoreKeeper.query.filter_by(is_approved=True).all()
    
    return render_template('user_management.html',
                         pending_storekeepers=pending_storekeepers,
                         approved_storekeepers=approved_storekeepers)


@admin_bp.route('/user-management/approve/<int:user_id>', methods=['POST'])
@login_required
def approve_storekeeper(user_id):
    """Approve a pending storekeeper"""
    storekeeper = StoreKeeper.query.get_or_404(user_id)
    
    if storekeeper.is_approved:
        flash('This storekeeper is already approved.', 'info')
    else:
        storekeeper.is_approved = True
        storekeeper.approved_at = datetime.utcnow
        db.session.commit()
        flash(f'Storekeeper "{storekeeper.full_name}" has been approved successfully.', 'success')
    
    return redirect(url_for('admin.user_management'))


@admin_bp.route('/user-management/reject/<int:user_id>', methods=['POST'])
@login_required
def reject_storekeeper(user_id):
    """Reject and delete a pending storekeeper"""
    storekeeper = StoreKeeper.query.get_or_404(user_id)
    full_name = storekeeper.full_name
    
    if storekeeper.is_approved:
        flash('Cannot reject an already approved storekeeper.', 'warning')
    else:
        db.session.delete(storekeeper)
        db.session.commit()
        flash(f'Storekeeper "{full_name}" has been rejected and removed.', 'success')
    
    return redirect(url_for('admin.user_management'))


@admin_bp.route('/user-management/deactivate/<int:user_id>', methods=['POST'])
@login_required
def deactivate_storekeeper(user_id):
    """Deactivate an approved storekeeper"""
    storekeeper = StoreKeeper.query.get_or_404(user_id)
    
    if not storekeeper.is_approved:
        flash('This storekeeper is not approved yet.', 'warning')
    else:
        storekeeper.is_approved = False
        storekeeper.approved_at = None
        db.session.commit()
        flash(f'Storekeeper "{storekeeper.full_name}" has been deactivated.', 'success')
    
    return redirect(url_for('admin.user_management'))
