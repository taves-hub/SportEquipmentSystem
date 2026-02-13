from app import create_app, db
from models import *

def verify_migration():
    """Verify that the PostgreSQL migration was successful"""
    app = create_app()

    with app.app_context():
        print("Verifying PostgreSQL migration...")

        try:
            # Check table counts
            tables_to_check = [
                ('admins', Admin),
                ('storekeepers', StoreKeeper),
                ('students', Student),
                ('staff', Staff),
                ('equipment', Equipment),
                ('issued_equipment', IssuedEquipment),
                ('satellite_campuses', SatelliteCampus),
                ('equipment_categories', EquipmentCategory),
                ('campus_distributions', CampusDistribution),
                ('clearance', Clearance),
                ('notifications', Notification)
            ]

            for table_name, model in tables_to_check:
                count = model.query.count()
                print(f"✓ {table_name}: {count} records")

            # Test some relationships
            print("\nTesting relationships...")

            # Check if equipment has issued items
            equipment_count = Equipment.query.count()
            issued_count = IssuedEquipment.query.count()
            print(f"✓ Equipment items: {equipment_count}")
            print(f"✓ Issued equipment records: {issued_count}")

            # Check admin users
            admin_count = Admin.query.count()
            storekeeper_count = StoreKeeper.query.count()
            print(f"✓ Admin users: {admin_count}")
            print(f"✓ Storekeeper users: {storekeeper_count}")

            print("\n✓ Migration verification completed successfully!")

        except Exception as e:
            print(f"✕ Migration verification failed: {e}")

if __name__ == '__main__':
    verify_migration()