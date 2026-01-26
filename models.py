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
    # Student fields
    student_id = db.Column(db.String(20), nullable=True)
    student_name = db.Column(db.String(100), nullable=True)
    student_email = db.Column(db.String(120), nullable=True)
    student_phone = db.Column(db.String(15), nullable=True)
    # Staff fields
    staff_payroll = db.Column(db.String(20), nullable=True)
    staff_name = db.Column(db.String(100), nullable=True)
    staff_email = db.Column(db.String(120), nullable=True)
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
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def get_id(self):
        return f"storekeeper-{self.id}"
