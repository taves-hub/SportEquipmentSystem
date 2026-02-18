-- Sports Equipment Management System
-- PostgreSQL Database Schema
-- Generated: February 13, 2026

-- ============================================================================
-- TABLE: admins
-- Description: Admin user accounts for system administration
-- ============================================================================
CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_admins_username ON admins(username);
CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);

-- ============================================================================
-- TABLE: satellite_campuses
-- Description: Satellite campus locations where equipment is distributed
-- ============================================================================
CREATE TABLE IF NOT EXISTS satellite_campuses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    location VARCHAR(200),
    code VARCHAR(20) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_satellite_campuses_code ON satellite_campuses(code);
CREATE INDEX IF NOT EXISTS idx_satellite_campuses_is_active ON satellite_campuses(is_active);

-- ============================================================================
-- TABLE: storekeepers
-- Description: Storekeeper user accounts (one per campus/satellite location)
-- ============================================================================
CREATE TABLE IF NOT EXISTS storekeepers (
    id SERIAL PRIMARY KEY,
    payroll_number VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(200) NOT NULL,
    campus_id INTEGER NOT NULL REFERENCES satellite_campuses(id),
    is_approved BOOLEAN DEFAULT FALSE NOT NULL,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_storekeepers_payroll_number ON storekeepers(payroll_number);
CREATE INDEX IF NOT EXISTS idx_storekeepers_email ON storekeepers(email);
CREATE INDEX IF NOT EXISTS idx_storekeepers_campus_id ON storekeepers(campus_id);
CREATE INDEX IF NOT EXISTS idx_storekeepers_is_approved ON storekeepers(is_approved);

-- ============================================================================
-- TABLE: students
-- Description: Student records for equipment issuance
-- ============================================================================
CREATE TABLE IF NOT EXISTS students (
    id VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
CREATE INDEX IF NOT EXISTS idx_students_name ON students(name);

-- ============================================================================
-- TABLE: staff
-- Description: Staff member records for equipment issuance
-- ============================================================================
CREATE TABLE IF NOT EXISTS staff (
    payroll_number VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_staff_email ON staff(email);
CREATE INDEX IF NOT EXISTS idx_staff_name ON staff(name);

-- ============================================================================
-- TABLE: equipment_categories
-- Description: Equipment categories and their codes
-- ============================================================================
CREATE TABLE IF NOT EXISTS equipment_categories (
    id SERIAL PRIMARY KEY,
    category_code VARCHAR(10) NOT NULL UNIQUE,
    category_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_equipment_categories_code ON equipment_categories(category_code);
CREATE INDEX IF NOT EXISTS idx_equipment_categories_is_active ON equipment_categories(is_active);

-- ============================================================================
-- TABLE: equipment
-- Description: Main equipment inventory
-- ============================================================================
CREATE TABLE IF NOT EXISTS equipment (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    category_code VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL,
    condition VARCHAR(50) DEFAULT 'Good',
    damaged_count INTEGER DEFAULT 0 NOT NULL,
    lost_count INTEGER DEFAULT 0 NOT NULL,
    serial_number VARCHAR(100) NOT NULL UNIQUE,
    date_received TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_equipment_name ON equipment(name);
CREATE INDEX IF NOT EXISTS idx_equipment_category_code ON equipment(category_code);
CREATE INDEX IF NOT EXISTS idx_equipment_serial_number ON equipment(serial_number);
CREATE INDEX IF NOT EXISTS idx_equipment_is_active ON equipment(is_active);

-- ============================================================================
-- TABLE: campus_distributions
-- Description: Equipment distributed from main inventory to satellite campuses
-- ============================================================================
CREATE TABLE IF NOT EXISTS campus_distributions (
    id SERIAL PRIMARY KEY,
    campus_id INTEGER NOT NULL REFERENCES satellite_campuses(id),
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    category_code VARCHAR(10) NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    quantity INTEGER NOT NULL,
    date_distributed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    distributed_by VARCHAR(120),
    notes TEXT,
    document_path VARCHAR(500)
);

CREATE INDEX IF NOT EXISTS idx_campus_distributions_campus_id ON campus_distributions(campus_id);
CREATE INDEX IF NOT EXISTS idx_campus_distributions_equipment_id ON campus_distributions(equipment_id);
CREATE INDEX IF NOT EXISTS idx_campus_distributions_date ON campus_distributions(date_distributed);

-- ============================================================================
-- TABLE: issued_equipment
-- Description: Equipment issues to students/staff with tracking details
-- ============================================================================
CREATE TABLE IF NOT EXISTS issued_equipment (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(20) REFERENCES students(id),
    staff_payroll VARCHAR(20) REFERENCES staff(payroll_number),
    equipment_id INTEGER NOT NULL REFERENCES equipment(id),
    quantity INTEGER NOT NULL,
    date_issued TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expected_return TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Issued',
    return_conditions TEXT,
    date_returned TIMESTAMP,
    damage_clearance_status VARCHAR(50),
    damage_clearance_notes TEXT,
    damage_clearance_document VARCHAR(500),
    issued_by VARCHAR(120),
    serial_numbers TEXT
);

CREATE INDEX IF NOT EXISTS idx_issued_equipment_student_id ON issued_equipment(student_id);
CREATE INDEX IF NOT EXISTS idx_issued_equipment_staff_payroll ON issued_equipment(staff_payroll);
CREATE INDEX IF NOT EXISTS idx_issued_equipment_equipment_id ON issued_equipment(equipment_id);
CREATE INDEX IF NOT EXISTS idx_issued_equipment_status ON issued_equipment(status);
CREATE INDEX IF NOT EXISTS idx_issued_equipment_date_issued ON issued_equipment(date_issued);
CREATE INDEX IF NOT EXISTS idx_issued_equipment_expected_return ON issued_equipment(expected_return);
CREATE INDEX IF NOT EXISTS idx_issued_equipment_issued_by ON issued_equipment(issued_by);

-- ============================================================================
-- TABLE: clearance
-- Description: Clearance status tracking for students
-- ============================================================================
CREATE TABLE IF NOT EXISTS clearance (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(20) NOT NULL UNIQUE,
    status VARCHAR(20) DEFAULT 'Pending Clearance',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clearance_student_id ON clearance(student_id);
CREATE INDEX IF NOT EXISTS idx_clearance_status ON clearance(status);

-- ============================================================================
-- TABLE: notifications
-- Description: System notifications for admins and storekeepers
-- ============================================================================
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    recipient_role VARCHAR(20) NOT NULL,
    recipient_id INTEGER,
    message TEXT NOT NULL,
    url VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notifications_recipient_role ON notifications(recipient_role);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient_id ON notifications(recipient_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

-- ============================================================================
-- FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- Ensure campus_id in storekeepers references valid satellite_campus
ALTER TABLE storekeepers
ADD CONSTRAINT fk_storekeepers_campus_id 
FOREIGN KEY (campus_id) REFERENCES satellite_campuses(id) ON DELETE RESTRICT;

-- Ensure equipment_id in issued_equipment references valid equipment
ALTER TABLE issued_equipment
ADD CONSTRAINT fk_issued_equipment_equipment_id 
FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE RESTRICT;

-- Ensure campus_id in campus_distributions references valid satellite_campus
ALTER TABLE campus_distributions
ADD CONSTRAINT fk_campus_distributions_campus_id 
FOREIGN KEY (campus_id) REFERENCES satellite_campuses(id) ON DELETE RESTRICT;

-- Ensure equipment_id in campus_distributions references valid equipment
ALTER TABLE campus_distributions
ADD CONSTRAINT fk_campus_distributions_equipment_id 
FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE RESTRICT;

-- ============================================================================
-- SAMPLE DATA (Optional - Uncomment to populate initial data)
-- ============================================================================

-- Insert main admin user (password must be hashed in application)
-- INSERT INTO admins (username, email, password_hash) 
-- VALUES ('admin', 'admin@university.ac.ke', 'hashed_password_here');

-- Insert sample satellite campuses
-- INSERT INTO satellite_campuses (name, location, code)
-- VALUES 
--   ('Main Campus', 'Nairobi CBD', 'MAIN'),
--   ('Parklands Campus', 'Parklands, Nairobi', 'PARK'),
--   ('Kabete Campus', 'Kabete, Nairobi', 'KABS');

-- Insert sample equipment categories
-- INSERT INTO equipment_categories (category_code, category_name, description)
-- VALUES 
--   ('ATH-001', 'Balls', 'Various sports balls'),
--   ('ATH-002', 'Protective Gear', 'Protective equipment for athletes'),
--   ('ATH-003', 'Training Equipment', 'General training and gym equipment');

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
