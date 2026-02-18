# Database Documentation
## Sports Equipment Management System

**Last Updated:** February 13, 2026  
**Database Type:** PostgreSQL  
**Database Name:** `sports_equipment_db`

---

## Table of Contents
1. [Database Overview](#database-overview)
2. [Connection Details](#connection-details)
3. [Schema Tables](#schema-tables)
4. [Relationships Diagram](#relationships-diagram)
5. [Data Dictionary](#data-dictionary)
6. [Backup and Restore](#backup-and-restore)
7. [Common Queries](#common-queries)

---

## Database Overview

The Sports Equipment Management System database is designed to manage the complete lifecycle of sports equipment distribution, issuance, and tracking across multiple satellite campuses of the University of Nairobi.

### Key Features:
- **Multi-campus Support**: Equipment distributed to multiple satellite campuses
- **User Roles**: Admin and Storekeeper accounts with different permissions
- **Complete Audit Trail**: Track all equipment movements and status changes
- **Damage Tracking**: Record and manage damaged/lost equipment
- **Clearance Management**: Monitor student/staff clearance status
- **Notifications System**: Automated alerts for admins and storekeepers

---

## Connection Details

### Server Information
- **Host**: localhost
- **Port**: 5432 (default PostgreSQL port)
- **Database**: sports_equipment_db
- **Username**: postgres
- **Password**: Taves254

### Connection String (Flask/SQLAlchemy)
```
postgresql://postgres:Taves254@localhost/sports_equipment_db
```

### Connecting with psql CLI
```bash
psql -h localhost -U postgres -d sports_equipment_db
```

---

## Schema Tables

### 1. **admins**
Stores administrator user accounts with login credentials.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique admin ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | Login username |
| password_hash | VARCHAR(200) | NOT NULL | Hashed password |
| email | VARCHAR(120) | UNIQUE, NOT NULL | Admin email address |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation date |

**Indexes:**
- `idx_admins_username` - For fast login lookups
- `idx_admins_email` - For email-based queries

---

### 2. **satellite_campuses**
Represents different campus locations where equipment is stored/distributed.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique campus ID |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Campus name (e.g., "Main Campus") |
| location | VARCHAR(200) | | Physical location address |
| code | VARCHAR(20) | UNIQUE, NOT NULL | Campus code (e.g., "MAIN", "PARK") |
| is_active | BOOLEAN | DEFAULT TRUE | Whether campus is operational |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation date |

**Indexes:**
- `idx_satellite_campuses_code` - For campus code lookups
- `idx_satellite_campuses_is_active` - For filtering active campuses

**Sample Data:**
```sql
INSERT INTO satellite_campuses (name, location, code) 
VALUES 
  ('Main Campus', 'Nairobi CBD', 'MAIN'),
  ('Parklands Campus', 'Parklands, Nairobi', 'PARK'),
  ('Kabete Campus', 'Kabete, Nairobi', 'KABS');
```

---

### 3. **storekeepers**
Storekeeper user accounts (staff responsible for equipment distribution at each campus).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique storekeeper ID |
| payroll_number | VARCHAR(20) | UNIQUE, NOT NULL | Employee payroll number (6 digits) |
| full_name | VARCHAR(100) | NOT NULL | Full name of storekeeper |
| email | VARCHAR(120) | UNIQUE, NOT NULL | Email address |
| password_hash | VARCHAR(200) | NOT NULL | Hashed password |
| campus_id | INTEGER | FK -> satellite_campuses(id) | Assigned campus |
| is_approved | BOOLEAN | DEFAULT FALSE | Whether admin approved account |
| approved_at | TIMESTAMP | | When account was approved |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Account creation date |

**Indexes:**
- `idx_storekeepers_payroll_number` - For payroll lookups
- `idx_storekeepers_email` - For email queries
- `idx_storekeepers_campus_id` - For campus-based queries
- `idx_storekeepers_is_approved` - For pending approvals

---

### 4. **students**
Student records for equipment issuance tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(20) | PRIMARY KEY | Student ID number |
| name | VARCHAR(100) | NOT NULL | Student full name |
| email | VARCHAR(120) | UNIQUE, NOT NULL | Student email |
| phone | VARCHAR(15) | | Contact phone number |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation date |

**Indexes:**
- `idx_students_email` - For email queries
- `idx_students_name` - For name searches

---

### 5. **staff**
Staff member records for equipment issuance tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| payroll_number | VARCHAR(20) | PRIMARY KEY | Staff payroll number |
| name | VARCHAR(100) | NOT NULL | Staff full name |
| email | VARCHAR(120) | UNIQUE, NOT NULL | Staff email |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation date |

**Indexes:**
- `idx_staff_email` - For email queries
- `idx_staff_name` - For name searches

---

### 6. **equipment_categories**
Equipment category definitions with codes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique category ID |
| category_code | VARCHAR(10) | UNIQUE, NOT NULL | Category code (e.g., "ATH-001") |
| category_name | VARCHAR(100) | NOT NULL | Category name (e.g., "Balls") |
| description | TEXT | | Category description |
| is_active | BOOLEAN | DEFAULT TRUE | Whether category is active |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Record creation date |

**Indexes:**
- `idx_equipment_categories_code` - For code-based lookups
- `idx_equipment_categories_is_active` - For active categories

---

### 7. **equipment**
Main equipment inventory at the institution.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique equipment ID |
| name | VARCHAR(100) | NOT NULL | Equipment name (e.g., "Basketball") |
| category | VARCHAR(50) | NOT NULL | Equipment category |
| category_code | VARCHAR(10) | NOT NULL | Category code reference |
| quantity | INTEGER | NOT NULL | Total quantity in inventory |
| condition | VARCHAR(50) | DEFAULT 'Good' | Overall condition status |
| damaged_count | INTEGER | DEFAULT 0 | Number of damaged items |
| lost_count | INTEGER | DEFAULT 0 | Number of lost items |
| serial_number | VARCHAR(100) | UNIQUE, NOT NULL | Unique serial number |
| date_received | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When received |
| is_active | BOOLEAN | DEFAULT TRUE | Whether item is active |

**Calculation Formula:**
```
Available Quantity = Total Quantity - Issued - Damaged - Lost
```

**Indexes:**
- `idx_equipment_name` - For equipment searches
- `idx_equipment_category_code` - For category filtering
- `idx_equipment_serial_number` - For serial lookups
- `idx_equipment_is_active` - For active items

---

### 8. **campus_distributions**
Tracks equipment distributed from main inventory to satellite campuses.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique distribution ID |
| campus_id | INTEGER | FK -> satellite_campuses(id) | Target campus |
| equipment_id | INTEGER | FK -> equipment(id) | Equipment item |
| category_code | VARCHAR(10) | NOT NULL | Equipment category code |
| category_name | VARCHAR(100) | NOT NULL | Equipment category name |
| quantity | INTEGER | NOT NULL | Quantity distributed |
| date_distributed | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Distribution date |
| distributed_by | VARCHAR(120) | | Admin who distributed |
| notes | TEXT | | Distribution notes |
| document_path | VARCHAR(500) | | Path to supporting document |

**Indexes:**
- `idx_campus_distributions_campus_id`
- `idx_campus_distributions_equipment_id`
- `idx_campus_distributions_date`

---

### 9. **issued_equipment**
Complete record of equipment issued to students/staff.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique issue ID |
| student_id | VARCHAR(20) | FK -> students(id) | Student (if applicable) |
| staff_payroll | VARCHAR(20) | FK -> staff(payroll_number) | Staff (if applicable) |
| equipment_id | INTEGER | FK -> equipment(id) | Equipment issued |
| quantity | INTEGER | NOT NULL | Quantity issued |
| date_issued | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Issue date |
| expected_return | TIMESTAMP | | Expected return date |
| status | VARCHAR(50) | DEFAULT 'Issued' | Issue status (Issued, Returned, etc.) |
| return_conditions | TEXT | | Condition upon return |
| date_returned | TIMESTAMP | | Actual return date |
| damage_clearance_status | VARCHAR(50) | | Clearance status (Repaired, Replaced, etc.) |
| damage_clearance_notes | TEXT | | Clearance notes |
| damage_clearance_document | VARCHAR(500) | | Path to clearance document |
| issued_by | VARCHAR(120) | | Username of issuer |
| serial_numbers | TEXT | | Serial numbers issued |

**Status Values:**
- `Issued` - Equipment currently issued
- `Returned` - Equipment returned in good condition
- `Partial Return` - Some items returned
- `Missing` - Equipment not returned

**Indexes:**
- `idx_issued_equipment_student_id`
- `idx_issued_equipment_staff_payroll`
- `idx_issued_equipment_equipment_id`
- `idx_issued_equipment_status`
- `idx_issued_equipment_date_issued`
- `idx_issued_equipment_expected_return`
- `idx_issued_equipment_issued_by`

---

### 10. **clearance**
Student clearance status tracking.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique clearance ID |
| student_id | VARCHAR(20) | UNIQUE, NOT NULL | Student reference |
| status | VARCHAR(20) | DEFAULT 'Pending Clearance' | Clearance status |
| last_updated | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update date |

**Status Values:**
- `Cleared` - All equipment returned in good condition
- `Pending` - Awaiting equipment return
- `Overdue` - Equipment not returned by expected date

**Indexes:**
- `idx_clearance_student_id`
- `idx_clearance_status`

---

### 11. **notifications**
System notifications for admins and storekeepers.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | SERIAL | PRIMARY KEY | Unique notification ID |
| recipient_role | VARCHAR(20) | NOT NULL | 'admin' or 'storekeeper' |
| recipient_id | INTEGER | | Storekeeper ID (NULL for admin broadcast) |
| message | TEXT | NOT NULL | Notification message |
| url | VARCHAR(500) | | Link to related resource |
| is_read | BOOLEAN | DEFAULT FALSE | Whether read by recipient |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Creation date |

**Indexes:**
- `idx_notifications_recipient_role`
- `idx_notifications_recipient_id`
- `idx_notifications_is_read`
- `idx_notifications_created_at`

---

## Relationships Diagram

```
admins (1) ─────────────────────> (many roles)

satellite_campuses (1) ─────┬────> (many) storekeepers
                            └────> (many) campus_distributions

storekeepers (1) ─────────────────> (many issued_equipment)

students (1) ────────────────────> (many) issued_equipment
                                        ↓
staff (1) ────────────────────────> (many) issued_equipment

equipment (1) ───────┬──────────────> (many) issued_equipment
                     ├──────────────> (many) campus_distributions
                     └──────────────> available_quantity (calculated)

equipment_categories (1) ─────────> (many) equipment

clearance (1:1) ─────────────────> (unique) students
```

---

## Data Dictionary

### Status Fields

#### issued_equipment.status
- **Issued** - Equipment currently in use
- **Returned** - Equipment returned
- **Partial Return** - Some equipment returned, some still outstanding
- **Missing** - Equipment not returned

#### issued_equipment.damage_clearance_status
- **Repaired** - Damage has been repaired
- **Replaced** - Item replaced with new one
- **Escalated** - Damage escalated to admin
- **NULL** - Not yet cleared

#### clearance.status
- **Cleared** - No outstanding items
- **Pending Clearance** - Awaiting equipment return
- **Overdue** - Past expected return date

---

## Backup and Restore

### Using the Database Utility Script

#### Line 1: Create a Backup
```bash
python database_utility.py backup
```
Automatically creates timestamped backup in `database_backups/` directory.

#### Restore from Backup
```bash
python database_utility.py restore database_backups/sports_equipment_db_backup_20260213_120000.sql
```

#### List All Backups
```bash
python database_utility.py list
```

#### Get Database Statistics
```bash
python database_utility.py stats
```

### Manual Backup with pg_dump
```bash
pg_dump -h localhost -U postgres -d sports_equipment_db > backup.sql
```

### Manual Restore with psql
```bash
psql -h localhost -U postgres -d sports_equipment_db < backup.sql
```

---

## Common Queries

### 1. Get All Equipment Available at a Campus
```sql
SELECT e.name, e.quantity - (e.damaged_count + e.lost_count) as available
FROM equipment e
JOIN campus_distributions cd ON e.id = cd.equipment_id
WHERE cd.campus_id = 1
AND e.is_active = TRUE;
```

### 2. Find Overdue Equipment Issues
```sql
SELECT ie.id, s.name, e.name, ie.expected_return
FROM issued_equipment ie
JOIN students s ON ie.student_id = s.id
JOIN equipment e ON ie.equipment_id = e.id
WHERE ie.status = 'Issued' 
AND ie.expected_return < NOW();
```

### 3. Get Storekeeper Assignments
```sql
SELECT sk.full_name, sk.payroll_number, sc.name, sc.code
FROM storekeepers sk
JOIN satellite_campuses sc ON sk.campus_id = sc.id
WHERE sk.is_approved = TRUE;
```

### 4. Equipment Damage Summary
```sql
SELECT name, damaged_count, lost_count, 
       (damaged_count + lost_count) as total_unusable
FROM equipment
WHERE (damaged_count + lost_count) > 0
ORDER BY total_unusable DESC;
```

### 5. Student Clearance Report
```sql
SELECT s.id, s.name, c.status, COUNT(ie.id) as outstanding_items
FROM students s
LEFT JOIN clearance c ON s.id = c.student_id
LEFT JOIN issued_equipment ie ON s.id = ie.student_id 
                              AND ie.status = 'Issued'
GROUP BY s.id, s.name, c.status;
```

### 6. Distribution History by Campus
```sql
SELECT sc.name, e.name, cd.quantity, cd.date_distributed, cd.distributed_by
FROM campus_distributions cd
JOIN satellite_campuses sc ON cd.campus_id = sc.id
JOIN equipment e ON cd.equipment_id = e.id
ORDER BY cd.date_distributed DESC;
```

---

## Performance Optimization

### Recommended Indexes
All recommended indexes have been created as part of the schema. They focus on:
- **Login Performance**: username and email lookups
- **Report Generation**: date and status filtering
- **Multi-campus queries**: campus_id filtering
- **Storekeeper operations**: equipment and status lookups

### Query Performance Tips
1. Always filter by `is_active = TRUE` for active records
2. Use `campus_id` index for campus-specific queries
3. Use `date_issued` index for date range queries
4. Use composite indexes for common multi-field filters

---

## Data Validation Rules

### Equipment
- Serial numbers must be unique
- Quantity cannot be negative
- damaged_count + lost_count ≤ quantity

### Issued Equipment
- Either student_id OR staff_payroll must be set (not both NULL)
- quantity > 0
- expected_return cannot be in the past for new issues

### Storekeepers
- Payroll number must be 6 digits (validated in app)
- Email must be unique
- campus_id must reference valid active campus

### Students/Staff
- Email must be unique
- IDs/payroll numbers must be valid formats

---

## Backup Schedule Recommendation

- **Daily**: Automatic backup via scheduled job
- **Weekly**: Full backup with long-term retention
- **Monthly**: Archive creation for compliance

---

**For Questions:** Contact System Administrator  
**Last Updated:** February 13, 2026
