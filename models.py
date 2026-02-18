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
    # Track damage/loss clearance: None, Repaired, Replaced, Escalated
    damage_clearance_status = db.Column(db.String(50), nullable=True)
    damage_clearance_notes = db.Column(db.Text, nullable=True)
    # Path to an attached admin document (stored file path)
    damage_clearance_document = db.Column(db.String(500), nullable=True)
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


class AccessLog(db.Model):
    __tablename__ = 'access_logs'
    id = db.Column(db.Integer, primary_key=True)  # 10. AUDIT TRAIL: Unique log entry ID
    user_id = db.Column(db.Integer, nullable=False)  # 1. USER IDENTIFICATION
    user_type = db.Column(db.String(20), nullable=False)  # 1. USER IDENTIFICATION: Role/Privilege Level
    username = db.Column(db.String(120), nullable=False)  # 1. USER IDENTIFICATION
    full_name = db.Column(db.String(120), nullable=True)  # 1. USER IDENTIFICATION: Full Name

    # 2. TIMESTAMP
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # Date & Time
    timezone = db.Column(db.String(10), default='UTC', nullable=False)  # Time zone

    # 3. SOURCE INFORMATION
    ip_address = db.Column(db.String(45), nullable=True)  # IP Address
    user_agent = db.Column(db.Text, nullable=True)  # Browser type, version, OS, Device type
    geolocation = db.Column(db.String(255), nullable=True)  # Geolocation (optional)

    # 4. ACTION PERFORMED
    action = db.Column(db.String(200), nullable=False)  # Event type & description
    endpoint = db.Column(db.String(255), nullable=True)  # Resource accessed (page URL)
    method = db.Column(db.String(10), nullable=False, default='GET')  # HTTP method
    status_code = db.Column(db.Integer, nullable=True)  # HTTP status code
    action_status = db.Column(db.String(20), default='Success', nullable=False)  # Success/Failure

    # 5. AUTHENTICATION DETAILS
    auth_method = db.Column(db.String(50), default='password', nullable=False)  # Authentication method
    session_id = db.Column(db.String(255), nullable=True)  # Session ID
    login_attempts = db.Column(db.Integer, default=0, nullable=False)  # Login attempt count
    mfa_used = db.Column(db.Boolean, default=False, nullable=False)  # MFA status

    # 6. SYSTEM/APPLICATION DETAILS
    app_name = db.Column(db.String(100), default='SportEquipmentSystem', nullable=False)  # Application name
    module = db.Column(db.String(100), nullable=True)  # Module/section accessed
    server_hostname = db.Column(db.String(255), nullable=True)  # Server/hostname
    protocol = db.Column(db.String(10), default='HTTP', nullable=False)  # Protocol used

    # 7. DATA MODIFICATION TRACKING
    data_changed = db.Column(db.Text, nullable=True)  # Before/after values
    record_id = db.Column(db.String(100), nullable=True)  # Record ID affected
    query_executed = db.Column(db.Text, nullable=True)  # Query executed

    # 8. SECURITY & COMPLIANCE
    access_level = db.Column(db.String(50), nullable=True)  # Access approval level
    alerts_triggered = db.Column(db.Text, nullable=True)  # Alerts triggered
    log_hash = db.Column(db.String(128), nullable=True)  # Log integrity check (hash)
    retention_days = db.Column(db.Integer, default=365, nullable=False)  # Retention period

    # 9. ADDITIONAL METADATA
    duration_ms = db.Column(db.Integer, nullable=True)  # Duration in milliseconds
    data_size_bytes = db.Column(db.Integer, nullable=True)  # Size of data transferred
    referrer_url = db.Column(db.String(500), nullable=True)  # Referrer URL

    # 10. AUDIT TRAIL REQUIREMENTS - Tamper-proof, searchable, secure
    is_tamper_proof = db.Column(db.Boolean, default=True, nullable=False)
    search_index = db.Column(db.Text, nullable=True)  # For enhanced searchability

    def __repr__(self):
        return f'<AccessLog {self.username} - {self.action} at {self.timestamp}>'

    def generate_log_hash(self):
        """Generate integrity hash for tamper-proof logging"""
        import hashlib
        log_data = f"{self.id}{self.user_id}{self.username}{self.timestamp}{self.action}{self.endpoint}"
        return hashlib.sha256(log_data.encode()).hexdigest()

    def to_dict(self):
        """Convert log entry to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_type': self.user_type,
            'username': self.username,
            'full_name': self.full_name,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'timezone': self.timezone,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'geolocation': self.geolocation,
            'action': self.action,
            'endpoint': self.endpoint,
            'method': self.method,
            'status_code': self.status_code,
            'action_status': self.action_status,
            'auth_method': self.auth_method,
            'session_id': self.session_id,
            'login_attempts': self.login_attempts,
            'mfa_used': self.mfa_used,
            'app_name': self.app_name,
            'module': self.module,
            'server_hostname': self.server_hostname,
            'protocol': self.protocol,
            'data_changed': self.data_changed,
            'record_id': self.record_id,
            'query_executed': self.query_executed,
            'access_level': self.access_level,
            'alerts_triggered': self.alerts_triggered,
            'log_hash': self.log_hash,
            'retention_days': self.retention_days,
            'duration_ms': self.duration_ms,
            'data_size_bytes': self.data_size_bytes,
            'referrer_url': self.referrer_url,
            'is_tamper_proof': self.is_tamper_proof
        }

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    recipient_role = db.Column(db.String(20), nullable=False)  # 'admin' or 'storekeeper'
    recipient_id = db.Column(db.Integer, nullable=True)  # storekeeper.id when applicable; NULL for admin broadcasts
    message = db.Column(db.Text, nullable=False)
    url = db.Column(db.String(500), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
