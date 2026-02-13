from werkzeug.security import generate_password_hash
from app import create_app, db
from models import StoreKeeper

def update_all_passwords():
    """Update all storekeeper passwords to Password123"""

    app = create_app()
    with app.app_context():
        print("Updating all storekeeper passwords to: Password123")

        # Hash the password
        password_hash = generate_password_hash('Password123')

        # Get all storekeepers
        storekeepers = StoreKeeper.query.all()

        # Update password for each storekeeper
        for storekeeper in storekeepers:
            storekeeper.password_hash = password_hash

        db.session.commit()

        print(f"\n✅ Successfully updated {len(storekeepers)} storekeeper passwords to: Password123")

        # Display updated storekeepers with new password
        print("\n" + "="*80)
        print("UPDATED STOREKEEPER LOGIN CREDENTIALS")
        print("="*80)

        storekeepers = StoreKeeper.query.all()
        for storekeeper in storekeepers:
            print(f"\nName: {storekeeper.full_name}")
            print(f"Payroll Number: {storekeeper.payroll_number}")
            print(f"Email: {storekeeper.email}")
            print(f"Password: Password123")
            print("-" * 40)

        print(f"\n📋 Total Storekeepers: {len(storekeepers)}")
        print("✅ All passwords updated to: Password123")

if __name__ == '__main__':
    update_all_passwords()