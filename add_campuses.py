from app import create_app, db
from models import SatelliteCampus

def add_university_campuses():
    """Add University of Nairobi satellite campuses"""

    app = create_app()
    with app.app_context():
        print("Adding University of Nairobi satellite campuses...")

        # Campus data with names, codes, and locations
        campuses_data = [
            {
                'name': 'Main Campus',
                'code': 'MAIN',
                'location': 'Main Campus, University of Nairobi'
            },
            {
                'name': 'Lower Kabete Campus',
                'code': 'LK',
                'location': 'Lower Kabete, Nairobi'
            },
            {
                'name': 'Kikuyu Campus',
                'code': 'KK',
                'location': 'Kikuyu, Kiambu County'
            },
            {
                'name': 'Kenyatta National Campus',
                'code': 'KNC',
                'location': 'Kenyatta National Hospital, Nairobi'
            },
            {
                'name': 'Parklands Campus',
                'code': 'PL',
                'location': 'Parklands, Nairobi'
            },
            {
                'name': 'Kenya Science Campus',
                'code': 'KSC',
                'location': 'Kenya Science Campus, Nairobi'
            }
        ]

        campuses_added = 0

        for campus_data in campuses_data:
            # Check if campus already exists
            existing = SatelliteCampus.query.filter_by(name=campus_data['name']).first()
            if not existing:
                campus = SatelliteCampus(
                    name=campus_data['name'],
                    location=campus_data['location'],
                    code=campus_data['code'],
                    is_active=True
                )
                db.session.add(campus)
                campuses_added += 1
                print(f"✓ Added campus: {campus_data['name']} ({campus_data['code']})")
            else:
                print(f"⚠ Campus already exists: {campus_data['name']}")

        db.session.commit()
        print(f"\n✅ Successfully added {campuses_added} University of Nairobi satellite campuses")

if __name__ == '__main__':
    add_university_campuses()