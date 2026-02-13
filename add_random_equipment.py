import random
import uuid
from datetime import datetime
from app import create_app, db
from models import Equipment, EquipmentCategory

def add_random_equipment():
    """Add equipment items with random quantities between 10-25"""

    app = create_app()
    with app.app_context():
        print("Adding random equipment with quantities 10-25...")

        # Define equipment categories and their items
        categories_data = [
            {
                'code': 'BSE-01',
                'name': 'Ball Sports Equipment',
                'items': ['Footballs', 'Basketballs', 'Volleyballs', 'Rugby balls', 'Handballs', 'Netballs']
            },
            {
                'code': 'NCE-02',
                'name': 'Net & Court Equipment',
                'items': ['Volleyball nets', 'Tennis nets', 'Badminton nets', 'Netball rings & nets', 'Court boundary lines']
            },
            {
                'code': 'ATE-03',
                'name': 'Athletics & Track Equipment',
                'items': ['Relay batons', 'Hurdles', 'Starting blocks', 'Shot put', 'Discus', 'Javelin', 'Measuring tapes']
            },
            {
                'code': 'ISE-04',
                'name': 'Indoor Sports Equipment',
                'items': ['Table tennis bats', 'Table tennis balls', 'Chess boards & pieces', 'Scrabble sets', 'Pool cues', 'Pool balls']
            },
            {
                'code': 'FSE-05',
                'name': 'Field & Team Sports Gear',
                'items': ['Hockey sticks', 'Cricket bats', 'Cricket balls', 'Baseball bats', 'Softballs', 'Lacrosse sticks']
            },
            {
                'code': 'FTE-06',
                'name': 'Fitness & Training Equipment',
                'items': ['Skipping ropes', 'Agility cones', 'Resistance bands', 'Medicine balls', 'Agility ladders', 'Speed hurdles']
            },
            {
                'code': 'PSE-07',
                'name': 'Protective & Safety Gear',
                'items': ['Shin guards', 'Helmets', 'Mouth guards', 'Knee pads', 'Elbow pads', 'Goalkeeper gloves']
            },
            {
                'code': 'AWE-08',
                'name': 'Apparel & Wearables',
                'items': ['Sports jerseys', 'Training bibs', 'Socks', 'Tracksuits', 'Training vests', 'T-shirts']
            }
        ]

        # Add categories if they don't exist
        for cat_data in categories_data:
            category = EquipmentCategory.query.filter_by(category_code=cat_data['code']).first()
            if not category:
                category = EquipmentCategory(
                    category_code=cat_data['code'],
                    category_name=cat_data['name'],
                    description=f"Equipment for {cat_data['name'].lower()}"
                )
                db.session.add(category)
                print(f"✓ Added category: {cat_data['code']} - {cat_data['name']}")

        db.session.commit()

        # Add equipment items
        equipment_added = 0
        for cat_data in categories_data:
            category = EquipmentCategory.query.filter_by(category_code=cat_data['code']).first()
            if category:
                for item_name in cat_data['items']:
                    # Generate random quantity between 10-25
                    quantity = random.randint(10, 25)

                    # Create unique serial number
                    serial_number = f"EQ-{uuid.uuid4().hex[:8].upper()}"

                    # Check if equipment already exists
                    existing = Equipment.query.filter_by(name=item_name, category_code=cat_data['code']).first()
                    if not existing:
                        equipment = Equipment(
                            name=item_name,
                            category=category.category_name,
                            category_code=cat_data['code'],
                            quantity=quantity,
                            condition='Good',
                            damaged_count=0,
                            lost_count=0,
                            is_active=True,
                            serial_number=serial_number,
                            date_received=datetime.utcnow()
                        )
                        db.session.add(equipment)
                        equipment_added += 1
                        print(f"✓ Added: {item_name} (Qty: {quantity}) - {cat_data['code']}")

        db.session.commit()
        print(f"\n✅ Successfully added {equipment_added} equipment items with random quantities (10-25)")

if __name__ == '__main__':
    add_random_equipment()