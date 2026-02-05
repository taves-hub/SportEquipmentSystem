from flask import Flask, redirect, url_for
from config import Config
from extensions import db, login_manager, migrate
from models import Admin, StoreKeeper

# User loader function
@login_manager.user_loader
def load_user(user_id):
    # user_id will be role-prefixed (e.g. 'admin-3' or 'storekeeper-2')
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

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    # Apply test overrides before initializing extensions
    if test_config:
        app.config.update(test_config)

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Import blueprints
    from routes.admin_routes import admin_bp
    from routes.auth_routes import auth_bp
    # storekeeper blueprint
    from routes.storekeeper_routes import storekeeper_bp

    # Register blueprints
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(storekeeper_bp)

    # Context processor for current time
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now()}

    # Custom Jinja2 filters
    @app.template_filter('from_json')
    def from_json_filter(value):
        import json
        if value and isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    # Add root route
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    with app.app_context():
        db.create_all()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
