from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, jsonify, session, abort
from flask_login import login_required, current_user
from extensions import db
from models import Admin, StoreKeeper, Equipment, IssuedEquipment, Clearance
from datetime import datetime, UTC, timedelta
from Utils.clearance_integration import update_clearance_status
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
    total_issued = IssuedEquipment.query.filter_by(status='Issued').count()
    total_cleared = Clearance.query.filter_by(status='Cleared').count()
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
        all_due_items.append({
            'recipient_id': it.staff_payroll or it.student_id,
            'recipient_name': it.staff_name or it.student_name,
            'recipient_email': it.staff_email or it.student_email,
            'recipient_phone': it.student_phone,
            'recipient_type': 'staff' if it.staff_name else 'student',
            'equipment_name': it.equipment.name if it.equipment else str(it.equipment_id),
            'equipment_id': it.equipment_id,
            'quantity': it.quantity,
            'expected_return': it.expected_return
        })

    due_count = len(due_items)

    return render_template('dashboard.html',
                           total_equipment=total_equipment,
                           total_issued=total_issued,
                           total_cleared=total_cleared,
                           due_count=due_count,
                           all_due_items=all_due_items)

@admin_bp.route('/equipment', methods=['GET', 'POST'])
@login_required
def equipment():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        category_code = request.form['category_code']
        quantity = request.form['quantity']
        
        # If category_code exists, increment quantity (consistent with bulk upload behavior)
        existing_code = Equipment.query.filter_by(category_code=category_code.upper()).first()
        try:
            qty = int(quantity)
        except Exception:
            qty = 0

        if existing_code:
            existing_code.quantity = (existing_code.quantity or 0) + qty
            db.session.add(existing_code)
            db.session.commit()
            flash(f'Existing equipment updated. Quantity increased by {qty}.', 'success')
        else:
            new_item = Equipment(
                name=name,
                category=category,
                category_code=category_code.upper(),  # Store in uppercase for consistency
                quantity=qty
            )
            db.session.add(new_item)
            db.session.commit()
            flash('Equipment added successfully!', 'success')
        return redirect(url_for('admin.equipment'))
    all_equipment = Equipment.query.order_by(Equipment.category.asc(), Equipment.name.asc()).all()
    return render_template('equipment.html', equipment=all_equipment)


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
            # Match existing equipment by BOTH category_code and name so different
            # equipment names under the same category_code are treated as distinct items.
            existing = Equipment.query.filter_by(category_code=category_code, name=name).first()
            if existing:
                existing.quantity = (existing.quantity or 0) + max(0, qty)
                db.session.add(existing)
                updated += 1
            else:
                new_item = Equipment(
                    name=name,
                    category=category or '',
                    category_code=category_code,
                    quantity=max(0, qty)
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

        # Match existing equipment by BOTH category_code and name so different
        # equipment names under the same category_code are treated as distinct items.
        existing = Equipment.query.filter_by(category_code=category_code, name=name).first()
        if existing:
            existing.quantity = (existing.quantity or 0) + max(0, qty)
            db.session.add(existing)
            updated += 1
        else:
            new_item = Equipment(
                name=name,
                category=category or '',
                category_code=category_code,
                quantity=max(0, qty)
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
    is_student = any(it.student_id for it in issued_items)
    is_staff = any(it.staff_payroll for it in issued_items)

    # Auto-evaluate clearance status per student and persist it (only for students)
    status_map = {}
    if is_student and not is_staff:
        student_ids = sorted({it.student_id for it in issued_items if it.student_id})
        for sid in student_ids:
            items_for_student = [it for it in issued_items if it.student_id == sid]
            # If any outstanding (not returned), pending
            if any(it.status != 'Returned' for it in items_for_student):
                new_status = 'Pending'
            else:
                # All returned: check for damaged/lost
                if any(any(c.lower() in ('damaged', 'lost') for c in json.loads(it.return_conditions or '{}').values()) for it in items_for_student):
                    new_status = 'Pending'
                else:
                    new_status = 'Cleared'

            status_map[sid] = new_status

            # Persist to Clearance table
            try:
                clearance = Clearance.query.filter_by(student_id=sid).first()
                if not clearance:
                    clearance = Clearance(student_id=sid)
                    db.session.add(clearance)
                if clearance.status != new_status:
                    clearance.status = new_status
                    clearance.last_updated = datetime.now(UTC)
                    db.session.add(clearance)
                    db.session.commit()
            except Exception:
                db.session.rollback()

    return render_template('clearance_report.html',
                           issued_items=issued_items,
                           student_id=recipient_id,
                           is_pdf=False,
                           clearance_status_map=status_map,
                           is_student=is_student,
                           is_staff=is_staff)


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
        recipient_name = issued_items[0].student_name or issued_items[0].staff_name or ''

    return render_template('clearance_report_print.html',
                           issued_items=issued_items,
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
        writer.writerow([
            item.staff_payroll or item.student_id,
            item.staff_name or item.student_name,
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
        if due_items[0].student_id == recipient_id:
            recipient_name = due_items[0].student_name
            recipient_type = 'Student'
        elif due_items[0].staff_payroll == recipient_id:
            recipient_name = due_items[0].staff_name
            recipient_type = 'Staff'
    
    # Get issuer info
    issuer_info = {}
    for item in due_items:
        if item.issued_by:
            admin = Admin.query.filter_by(username=item.issued_by).first()
            if admin:
                issuer_info[item.id] = {'name': admin.username, 'email': admin.email, 'id': admin.id}
            else:
                storekeeper = StoreKeeper.query.filter_by(username=item.issued_by).first()
                if storekeeper:
                    issuer_info[item.id] = {'name': storekeeper.username, 'email': storekeeper.email, 'id': storekeeper.id}
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
        for issue in IssuedEquipment.query.filter(IssuedEquipment.serial_number.isnot(None)):
            try:
                serials = json.loads(issue.serial_number)
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
    issue = IssuedEquipment(
        # Some DB schemas may have student_id NOT NULL; use empty string for staff issues
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
        update_clearance_status(issue.student_id)
        flash(f'Item returned successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error processing return. Please try again.', 'danger')
        return redirect(url_for('admin.return_item', issue_id=issue_id))

    return redirect(url_for('admin.issued_equipment'))


@admin_bp.route('/issued-equipment')
@login_required
def issued_equipment():
    issued = IssuedEquipment.query.order_by(IssuedEquipment.date_issued.desc()).all()
    return render_template('issued_equipment.html', issued=issued)


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


@admin_bp.route('/return-equipment', methods=['GET', 'POST'])
@login_required
def return_equipment():
    """Return Equipment module: select student/staff and display all their issued equipment"""
    recipient_id = request.args.get('recipient_id', '').strip()
    
    if request.method == 'POST':
        # Handle return of selected items
        selected_serials = request.form.getlist('selected_serials')
        if not selected_serials:
            flash('No items selected for return.', 'warning')
            return redirect(url_for('admin.return_equipment', recipient_id=recipient_id))
        
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
        
        return redirect(url_for('admin.return_equipment', recipient_id=recipient_id))
    
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


@admin_bp.route('/reports')
@login_required
def reports():
    total_equipment = Equipment.query.count()
    issued_count = IssuedEquipment.query.filter_by(status='Issued').count()
    returned_count = IssuedEquipment.query.filter_by(status='Returned').count()
    cleared_students = Clearance.query.filter_by(status='Cleared').count()

    return render_template(
        'reports.html',
        total_equipment=total_equipment,
        issued_count=issued_count,
        returned_count=returned_count,
        cleared_students=cleared_students
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
                    storekeeper = StoreKeeper.query.filter_by(username=item.issued_by).first()
                    if storekeeper:
                        issuer_info[item.id] = {'name': storekeeper.username, 'email': storekeeper.email, 'id': storekeeper.id}
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
            writer.writerow([
                issue.staff_payroll or issue.student_id,
                issue.staff_name or issue.student_name,
                (issue.staff_email or issue.student_email) or '—',
                issue.student_phone or '—',
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
                storekeeper = StoreKeeper.query.filter_by(username=item.issued_by).first()
                if storekeeper:
                    issuer_info[item.id] = {'name': storekeeper.username, 'email': storekeeper.email, 'id': storekeeper.id}
                else:
                    issuer_info[item.id] = {'name': item.issued_by, 'email': '—', 'id': '—'}
        else:
            issuer_info[item.id] = {'name': '—', 'email': '—', 'id': '—'}

    return render_template('issued_report.html', issued_items=items, equipments=equipments, selected_equipment=equipment_id, page=page, per_page=per_page, total=total, total_pages=total_pages, issuer_info=issuer_info)

@admin_bp.route('/returned_report')
@login_required
def returned_report():
    # Allow filtering by return condition via query string: ?condition=Good|Damaged|Lost|All
    condition = request.args.get('condition', 'All')
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    try:
        per_page = int(request.args.get('per_page', 25))
    except ValueError:
        per_page = 25
    export = request.args.get('export')

    base_q = IssuedEquipment.query.filter_by(status='Returned')
    if condition and condition != 'All':
        base_q = base_q.filter_by(return_condition=condition)

    total = base_q.count()
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1

    # Export full filtered results
    if export in ('csv', 'excel'):
        items = base_q.order_by(IssuedEquipment.date_returned.desc()).all()
        import csv
        from io import StringIO
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['Recipient ID', 'Recipient Name', 'Equipment Name', 'Category', 'Quantity', 'Date Issued', 'Date Returned', 'Return Condition'])
        for issue in items:
            writer.writerow([
                issue.staff_payroll or issue.student_id,
                issue.staff_name or issue.student_name,
                issue.equipment.name if issue.equipment else issue.equipment_id,
                issue.equipment.category if issue.equipment else '',
                issue.quantity,
                issue.date_issued.strftime('%Y-%m-%d'),
                issue.date_returned.strftime('%Y-%m-%d') if issue.date_returned else '',
                issue.return_condition or ''
            ])
        output = si.getvalue()
        si.close()
        from flask import Response
        if export == 'csv':
            mimetype = 'text/csv'
            fname = 'returned_items.csv'
        else:
            mimetype = 'application/vnd.ms-excel'
            fname = 'returned_items.xls'
        return Response(output, mimetype=mimetype, headers={"Content-Disposition": f"attachment;filename={fname}"})

    items = base_q.order_by(IssuedEquipment.date_returned.desc()).offset((page-1)*per_page).limit(per_page).all()

    return render_template('returned_report.html', returned_items=items, selected_condition=condition, page=page, per_page=per_page, total=total, total_pages=total_pages)


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
    page = request.args.get('page', 1, type=int)
    per_page = 10
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

    # Handle export (unpaginated full filtered results)
    if export_format:
        items = base_q.order_by(Equipment.category, Equipment.name).all()
        output = io.StringIO()
        writer = csv.writer(output)
        # Write headers
        writer.writerow(['ID', 'Name', 'Category', 'Category Code', 'Total Quantity', 'Available', 'Issued', 'Damaged', 'Lost'])
        # Write data
        for item in items:
            writer.writerow([
                item.id,
                item.name,
                item.category,
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

    # For normal page view (paginated)
    total = base_q.count()
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 1
    equipments = base_q.order_by(Equipment.category, Equipment.name) \
                      .offset((page-1)*per_page) \
                      .limit(per_page) \
                      .all()

    for equipment in equipments:
        equipment.issued_count = equipment.issued_items.filter_by(status='Issued').count()

    return render_template('equipment_report.html',
                         equipments=equipments,
                         search_name=search_name,
                         pagination={"page": page, "per_page": per_page,
                                     "total": total, "total_pages": total_pages,
                                     "has_prev": page > 1,
                                     "has_next": page < total_pages,
                                     "prev_num": page - 1,
                                     "next_num": page + 1,
                                     "iter_pages": lambda: range(1, total_pages + 1)})
