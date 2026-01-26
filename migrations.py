"""Helper script to set up and run Flask-Migrate operations"""
from flask_migrate import Migrate
from app import create_app
from extensions import db

# Create the Flask application
app = create_app()

# Initialize Flask-Migrate
migrate = Migrate(app, db)

if __name__ == '__main__':
    # This allows us to run Flask-Migrate commands directly
    with app.app_context():
        print("✓ Flask-Migrate initialized")
        print("Now you can run:")
        print("flask db init")
        print("flask db migrate -m 'Add return conditions and equipment counts'")
        print("flask db upgrade")