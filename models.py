from extensions import db
from flask_login import UserMixin
from datetime import datetime

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    def get_id(self):
        # return a prefixed id so user_loader can distinguish Admin vs StoreKeeper
        return f"admin-{self.id}"

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.String(20), primary_key=True)  # Student ID as primary key
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    
    # Relationship to issued equipment
    issued_items = db.relationship('IssuedEquipment', backref='student', lazy='dynamic')

class Staff(db.Model):
    __tablename__ = 'staff'
    payroll_number = db.Column(db.String(20), primary_key=True)  # Payroll number as primary key
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    
    # Relationship to issued equipment
    issued_items = db.relationship('IssuedEquipment', backref='staff', lazy='dynamic')

class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    category_code = db.Column(db.String(10), nullable=False)  # Code for category (not unique: multiple equipment names may share a code)
    quantity = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(50), default='Good')
    # Track damaged and lost items separately from available quantity
    damaged_count = db.Column(db.Integer, default=0, nullable=False)
    lost_count = db.Column(db.Integer, default=0, nullable=False)
    date_received = db.Column(db.DateTime, default=datetime.utcnow)
    # Admin-controlled active flag: when false the equipment is disabled and cannot be issued
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    # Serial number for the equipment; make unique and required
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    
    @property
    def available_quantity(self):
        """Calculate available quantity as total minus issued, damaged and lost."""
        try:
            issued_count = self.issued_items.filter_by(status='Issued').count()
        except Exception:
            # In some contexts (e.g., when object is not attached to session), fallback
            issued_count = 0
        return (self.quantity or 0) - issued_count - (self.damaged_count or 0) - (self.lost_count or 0)

class IssuedEquipment(db.Model):
    __tablename__ = 'issued_equipment'
    id = db.Column(db.Integer, primary_key=True)
    # Foreign keys to student and staff tables
    student_id = db.Column(db.String(20), db.ForeignKey('students.id'), nullable=True)
    staff_payroll = db.Column(db.String(20), db.ForeignKey('staff.payroll_number'), nullable=True)
    # Common fields
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    quantity = db.Column(db.Integer, nullable=False)
    date_issued = db.Column(db.DateTime, default=datetime.utcnow)
    expected_return = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='Issued')
    # Condition recorded when equipment is returned: Good, Damaged, Lost
    return_conditions = db.Column(db.Text, nullable=True)
    date_returned = db.Column(db.DateTime, nullable=True)
    # Track which user created the issue (admin or storekeeper username)
    issued_by = db.Column(db.String(120), nullable=True)
    serial_numbers = db.Column(db.Text, nullable=True)

    # Relationship to access equipment details easily (e.g., issue.equipment.name)
    equipment = db.relationship('Equipment', backref=db.backref('issued_items', lazy='dynamic'))

class Clearance(db.Model):
    __tablename__ = 'clearance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Pending Clearance')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)


class StoreKeeper(UserMixin, db.Model):
    __tablename__ = 'storekeepers'
    id = db.Column(db.Integer, primary_key=True)
    payroll_number = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    campus_id = db.Column(db.Integer, db.ForeignKey('satellite_campuses.id'), nullable=False)
    is_approved = db.Column(db.Boolean, default=False, nullable=False)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    campus = db.relationship('SatelliteCampus', backref='storekeepers')

    def get_id(self):
        return f"storekeeper-{self.id}"


class SatelliteCampus(db.Model):
    __tablename__ = 'satellite_campuses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    location = db.Column(db.String(200), nullable=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class EquipmentCategory(db.Model):
    __tablename__ = 'equipment_categories'
    id = db.Column(db.Integer, primary_key=True)
    category_code = db.Column(db.String(10), nullable=False, unique=True)
    category_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CampusDistribution(db.Model):
    __tablename__ = 'campus_distributions'
    id = db.Column(db.Integer, primary_key=True)
    campus_id = db.Column(db.Integer, db.ForeignKey('satellite_campuses.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    category_code = db.Column(db.String(10), nullable=False)
    category_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    date_distributed = db.Column(db.DateTime, default=datetime.utcnow)
    distributed_by = db.Column(db.String(120), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    document_path = db.Column(db.String(500), nullable=True)  # Path to uploaded supporting document
    
    # Relationships
    campus = db.relationship('SatelliteCampus', backref='distributions')
    equipment = db.relationship('Equipment', backref='campus_distributions')
