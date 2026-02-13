from app import create_app, db
from models import SatelliteCampus

def update_campus_codes():
    """Update campus codes to be numeric"""

    app = create_app()
    with app.app_context():
        print("Updating campus codes to numeric format...")

        # Map of campus names to numeric codes
        campus_codes = {
            'Main Campus': '001',
            'Lower Kabete Campus': '002',
            'Kikuyu Campus': '003',
            'Kenyatta National Campus': '004',
            'Parklands Campus': '005',
            'Kenya Science Campus': '006'
        }

        for campus_name, numeric_code in campus_codes.items():
            campus = SatelliteCampus.query.filter_by(name=campus_name).first()
            if campus:
                campus.code = numeric_code
                db.session.commit()
                print(f"✓ Updated {campus_name}: {numeric_code}")

        print("\n✅ All campus codes updated to numeric format")

        # Display updated campuses
        print("\nUpdated Campuses:")
        campuses = SatelliteCampus.query.all()
        for campus in campuses:
            print(f"{campus.code}: {campus.name}")

if __name__ == '__main__':
    update_campus_codes()