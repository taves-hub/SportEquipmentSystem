from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models import Admin, StoreKeeper
from extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        print(f"Login attempt - Username: {username}")
        # Try to find an Admin first, then a StoreKeeper
        user = Admin.query.filter_by(username=username).first()
        role = 'admin'
        if not user:
            user = StoreKeeper.query.filter_by(username=username).first()
            role = 'storekeeper' if user else role

        if user:
            print("User found in database")
            is_valid = check_password_hash(user.password_hash, password)
            print(f"Password valid: {is_valid}")
            if is_valid:
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
            flash('Username not found', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))
