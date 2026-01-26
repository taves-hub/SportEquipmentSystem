# Sport Equipment System — Project Specification

## Overview
A lightweight Flask-based equipment management system for issuing, returning, and reporting sports equipment to students. Key features:
- Inventory management (receive, enable/disable, quantities)
- Issue / return workflow with condition tracking (Good, Damaged, Lost)
- Reports: equipment inventory, issued items, returned items
- CSV export and client-side Print-to-PDF support
- Simple role-protected admin routes (Flask-Login)

This document summarizes the codebase structure, data models, API/route contracts, deployment and developer setup, quality gates, and recommended next steps.

---

## Tech stack
- Python 3.11+ (project uses Python 3.13 in environment logs — confirm local interpreter)
- Flask (Blueprints, Jinja2 templates)
- SQLAlchemy ORM
- Flask-Migrate / Alembic for DB migrations
- MySQL (pymysql) in current setup — earlier experiments with PostgreSQL were reverted
- HTML5 + Bootstrap 5 for frontend
- pytest for tests (repository includes `tests/`)


## Repo layout (important files)
- `app.py` — application factory / entry
- `config.py` — environment config and DB URI
- `extensions.py` — db, login, other extensions
- `models.py` — SQLAlchemy models (Equipment, IssuedEquipment, Clearance)
- `routes/` — Blueprint route handlers (`admin_routes.py`, `auth_routes.py`)
- `templates/` — Jinja2 templates for pages and reports
- `migrations/` — Alembic migration scripts
- `scripts/` and `Utils/` — helpers and checks
- `tests/` — automated tests
- `create_db.py`, `init_db.py`, `apply_migrations.py`, etc. — DB helpers


## Data model summary
(Only fields relevant to current features.)

Equipment
- `id` (int, PK)
- `name` (string, indexed)
- `category` (string)
- `category_code` (string, max 10, unique, stored uppercase)  <-- recently added
- `quantity` (int) — total units in inventory
- `damaged_count` (int)
- `lost_count` (int)
- `is_active` (bool)
- `date_received` (datetime)

IssuedEquipment
- `id` (int, PK)
- `student_id` (string)
- `student_name` (string)
- `equipment_id` (FK -> Equipment.id)
- `quantity` (int)
- `status` (string) — 'Issued' | 'Returned'
- `date_issued`, `date_returned` (datetime)
- `return_condition` (string) — 'Good' | 'Damaged' | 'Lost'
- `expected_return` (date)

Clearance
- `id`, `student_id`, `status` (Cleared / Not Cleared) and helper fields (used in clearance integration)


## Routes and behavior (admin Blueprint)
Only essential endpoints are listed (use `routes/admin_routes.py` for full details):

- `GET|POST /admin/equipment` — list equipment; POST to add new equipment. When adding, `category_code` is required and validated for uniqueness. Codes are normalized to uppercase before saving.

- `POST /admin/equipment/<id>/toggle` — enable/disable equipment (is_active).

- `GET|POST /admin/issue` — issue workflow. GET shows form. POST creates an IssuedEquipment record, decrements Equipment.quantity. Validation:
  - student id/name required
  - equipment must exist and have enough quantity
  - student cannot have unreturned items (project includes `Utils.student_checks.has_unreturned_items`)
  - expected_return must not be in the past

- `GET /admin/return/<issue_id>` & POST to return: updates issue.status -> 'Returned', sets `return_condition`, updates Equipment counts (increment `quantity` for Good; increment `damaged_count` or `lost_count` for Damaged/Lost).

- `GET /admin/equipment-report` — paginated equipment inventory; supports search by name or `category_code`. Export CSV is available; Print PDF button triggers `window.print()` client-side.

- `GET /admin/issued_report` — issued items listing, filter by equipment_id. Export CSV available; Print PDF triggers `window.print()`.

- `GET /admin/returned_report` — returned items listing, filter by return condition. Export CSV available; Print PDF triggers `window.print()`.

- API endpoints:
  - `/admin/api/inventory_top` — returns top-N equipment with counts (labels include category code now)
  - `/admin/api/return_conditions` — counts grouped by return condition
  - `/admin/api/issues_timeseries` — time series of issued/returned counts


## Frontend (templates) notes
- `templates/issue.html` — `select[name=equipment_id]` now displays `Category (Equipment Name) - Available: X` to help selection.
- `templates/equipment.html` — form includes `category_code` input with HTML5 validation (pattern `[A-Za-z0-9]+`, maxlength=10) and placeholder `FTB01`.
- Reports (`equipment_report.html`, `issued_report.html`, `returned_report.html`) show `category_code` where applicable and have `Export CSV` + `Print PDF` button (client-side print). The Print button uses `onclick="window.print()"`.


## Validation rules
- `category_code`: required, alphanumeric only, max length 10, unique; saved uppercase server-side.
- `quantity` field: integer, min 1 on form.
- `expected_return`: date >= today.
- Issue flow: cannot issue if equipment.quantity < requested quantity.
- Return flow: `return_condition` must be one of Good/Damaged/Lost.


## Migrations & DB notes
- Alembic is used via Flask-Migrate. Common commands (PowerShell):

```powershell
# generate a migration (autogenerate)
flask db migrate -m "your message"
# apply migrations
flask db upgrade
# if DB schema and migration history disagree, stamping may be used carefully:
flask db stamp head
```

- Note: During migration runs the repository had an error applying an earlier migration (duplicate column). The practical workaround used was to `flask db stamp head` to mark migrations as applied, then create the new migration for `category_code`, and run `flask db upgrade`. Only use `stamp` when you're sure the DB schema already matches the migrations — stamping can hide true drift if used incorrectly.


## Setup & local run (Windows PowerShell)
1. Create a virtualenv and install deps:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Configure DB connection in `config.py` (or via env variables if configurable). Current project uses MySQL/pymysql. Example MySQL URI:

```python
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://dbuser:dbpass@localhost/sport_equipment'
```

3. Create DB (either manually in MySQL or using provided helper):

```powershell
python create_db.py  # if present and configured
```

4. Initialize/apply migrations:

```powershell
flask db migrate -m "initial"
flask db upgrade
```

5. Run app (development):

```powershell
$env:FLASK_APP='app.py'; $env:FLASK_ENV='development'; flask run
```


## Tests
- Tests are under `tests/` — run with pytest:

```powershell
.\.venv\Scripts\Activate.ps1
pytest -q
# or run a specific test file
pytest tests/test_issue_workflow.py -q
```

Notes: Some earlier attempts to run tests via the automated runner showed no tests discovered when passing an incorrect path; run pytest from project root.


## API Contracts & data shapes
- Equipment (JSON)
```json
{
  "id": 12,
  "name": "Ball",
  "category": "Football",
  "category_code": "FTB01",
  "quantity": 10,
  "damaged_count": 0,
  "lost_count": 0,
  "is_active": true
}
```

- IssuedEquipment (JSON)
```json
{
  "id": 42,
  "student_id": "S12345",
  "student_name": "Jane Doe",
  "equipment_id": 12,
  "quantity": 1,
  "status": "Issued",
  "date_issued": "2025-11-12T10:00:00",
  "expected_return": "2025-11-20"
}
```

Endpoints usually return HTML pages; CSV exports return `text/csv` with appropriate headers. The API endpoints return JSON.


## Error modes and edge cases
- Duplicate `category_code` on create: server checks and flashes error; returns 302 to equipment page.
- Migration errors (duplicate columns): can occur when migrations are re-run against a schema that already has the fields. Remedies: inspect DB, revert/clean duplicate migration scripts, or use `flask db stamp` with caution.
- Issuing more than available quantity: blocked with a flash error.
- Student with unreturned items: issue blocked; `Utils.student_checks.has_unreturned_items` used to enforce.
- Returning item twice: prevented — code checks `issue.status` and warns user.


## Security & Permissions
- Routes in `admin_bp` are decorated with `@login_required` (Flask-Login). The project assumes a separate admin login flow and admin user management scripts (`create_admin.py`, `verify_admin.py`).


## Recent changes / changelog (high-level)
- Reverted PostgreSQL experiment and kept MySQL (pymysql) as primary DB.
- Added `category_code` (unique) to `Equipment` model plus HTML form validation and migration.
- Reordered fields in `templates/equipment.html` (Category, Category Code, Equipment Name).
- Changed `templates/issue.html` equipment select to show `Category (Equipment Name)`.
- Reports (`equipment_report`, `issued_report`, `returned_report`) updated to show `category_code` where useful; CSV exports updated to include it.
- Replaced "Export Excel" with a client-side "Print PDF" button (calls `window.print()`) in multiple report templates.
- Search in `equipment_report` updated to allow searching by `category_code` as well as name.


## Acceptance criteria (examples)
- Adding equipment with a duplicate `category_code` should fail with a helpful message.
- Issuing an item should decrement inventory; returning an item should update `damaged_count`/`lost_count`/`quantity` appropriately.
- Equipment report search should return matches for `category_code` partial matches.
- Print PDF button opens a print dialog and users can save a PDF from the browser.


## Recommended next steps / improvements
1. Add a print stylesheet (`static/css/print.css` with `@media print`) or a dedicated print template to optimize PDF layout and hide UI controls.
2. Server-side PDF generation when a downloadable file is required (WeasyPrint for HTML->PDF or wkhtmltopdf). Add a route like `/admin/equipment-report/print` to return a PDF.
3. Add an Import CSV feature (bulk create equipment) with validation and duplicate handling.
4. Add integration tests that exercise the issue/return/report flows and CSV/print flows.
5. Add stricter server-side validation for `category_code` (regex check) and return clear JSON errors for API calls.
6. Add role-based access control if different admin roles are needed.


## Contact / Notes
- File created: `docs/PROJECT_SPEC.md` (this document). Edit as needed.
- If you want a trimmed PDF-friendly output, I can add the `@media print` stylesheet and hide controls (pagination, buttons) so printouts are concise.

---

Document prepared on: 2025-11-12

