from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from models import Admin, StoreKeeper, SatelliteCampus
from extensions import db
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['username']  # Can be payroll number or admin username
        password = request.form['password']
        
        print(f"Login attempt - Input: {login_input}")
        # Try to find an Admin first, then a StoreKeeper
        user = Admin.query.filter_by(username=login_input).first()
        role = 'admin'
        if not user:
            user = StoreKeeper.query.filter_by(payroll_number=login_input).first()
            role = 'storekeeper' if user else role

        if user:
            print("User found in database")
            is_valid = check_password_hash(user.password_hash, password)
            print(f"Password valid: {is_valid}")
            if is_valid:
                # Check if storekeeper is approved
                if role == 'storekeeper' and not user.is_approved:
                    print("Storekeeper not approved")
                    flash('Your account is pending approval from the admin. Please check back later.', 'warning')
                else:
                    login_user(user)
                    print("User logged in successfully")
                    if role == 'admin':
                        return redirect(url_for('admin.dashboard'))
                    else:
                        return redirect(url_for('storekeeper.dashboard'))
            else:
                print("Invalid password")
                flash('Invalid password', 'danger')
        else:
            print("User not found")
            flash('Payroll number or username not found', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Storekeeper registration page"""
    if request.method == 'POST':
        payroll_number = request.form['payroll_number'].strip()
        full_name = request.form['full_name'].strip()
        email = request.form['email'].strip()
        campus_id = request.form['campus_id']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if not payroll_number or not full_name or not email or not campus_id or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('auth.register'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if payroll number already exists
        existing_payroll = StoreKeeper.query.filter_by(payroll_number=payroll_number).first()
        if existing_payroll:
            flash('This payroll number is already registered.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if email already exists
        existing_email = StoreKeeper.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered. Please use a different email.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Verify campus exists
        campus = SatelliteCampus.query.get(campus_id)
        if not campus or not campus.is_active:
            flash('Invalid or inactive campus selected.', 'danger')
            return redirect(url_for('auth.register'))
        
        try:
            # Create new storekeeper account (not approved by default)
            new_storekeeper = StoreKeeper(
                payroll_number=payroll_number,
                full_name=full_name,
                email=email,
                campus_id=int(campus_id),
                password_hash=generate_password_hash(password),
                is_approved=False,
                created_at=datetime.utcnow()
            )
            db.session.add(new_storekeeper)
            db.session.commit()
            
            flash('Registration successful! Your account is now pending admin approval. You will receive a notification once approved.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'danger')
            return redirect(url_for('auth.register'))
    
    # Get active campuses for dropdown
    campuses = SatelliteCampus.query.filter_by(is_active=True).order_by(SatelliteCampus.name).all()
    return render_template('register.html', campuses=campuses)
