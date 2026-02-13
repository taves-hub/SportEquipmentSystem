import os
import pymysql
from flask import Flask, redirect, url_for, send_from_directory
from config import Config
from extensions import db, login_manager, migrate
from models import Admin, StoreKeeper
from werkzeug.security import generate_password_hash

# MySQL compatibility
pymysql.install_as_MySQLdb()

# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    try:
        if not user_id:
            return None
        if isinstance(user_id, bytes):
            user_id = user_id.decode()
        if user_id.startswith('admin-'):
            uid = int(user_id.split('-', 1)[1])
            return db.session.get(Admin, uid)
        if user_id.startswith('storekeeper-'):
            uid = int(user_id.split('-', 1)[1])
            return db.session.get(StoreKeeper, uid)
    except Exception:
        return None
    return None

# Application factory
def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    # Apply test overrides
    if test_config:
        app.config.update(test_config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from routes.admin_routes import admin_bp
    from routes.auth_routes import auth_bp
    from routes.storekeeper_routes import storekeeper_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(storekeeper_bp)

    # Context processor to inject current datetime
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now()}

    # Custom Jinja2 filter
    @app.template_filter('from_json')
    def from_json_filter(value):
        import json
        if value and isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    # Root route
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # Serve uploaded files
    @app.route('/uploads/<path:filepath>')
    def serve_upload(filepath):
        uploads_dir = os.path.join(app.root_path, 'uploads')
        return send_from_directory(uploads_dir, filepath)

    # Ensure database tables exist
    with app.app_context():
        db.create_all()
        
        # Auto-create admin user if not exists
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user created automatically on startup!")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("! Admin user already exists")

    return app

# Create app instance at module level for Gunicorn and Flask CLI
app = create_app()

# Run locally
if __name__ == "__main__":
    app.run(debug=True)
