"""Seed equipment items for all sports equipment categories."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from extensions import db
from models import Equipment

app = create_app()
with app.app_context():
    try:
        # Equipment items organized by category code
        equipment_data = {
            "BSE-01": {
                "category_name": "Ball Sports Equipment",
                "items": [
                    "Footballs (Size 5)",
                    "Footballs (Size 4)",
                    "Basketballs",
                    "Volleyballs",
                    "Rugby balls",
                    "Handballs",
                    "Netballs",
                ]
            },
            "NCE-02": {
                "category_name": "Net & Court Equipment",
                "items": [
                    "Volleyball nets",
                    "Tennis nets",
                    "Badminton nets",
                    "Netball rings & nets",
                    "Court boundary lines",
                ]
            },
            "ATE-03": {
                "category_name": "Athletics & Track Equipment",
                "items": [
                    "Relay batons",
                    "Hurdles",
                    "Starting blocks",
                    "Shot put",
                    "Discus",
                    "Javelin",
                    "Measuring tapes",
                ]
            },
            "ISE-04": {
                "category_name": "Indoor Sports Equipment",
                "items": [
                    "Table tennis bats",
                    "Table tennis balls",
                    "Chess boards & pieces",
                    "Scrabble sets",
                    "Pool cues",
                    "Pool balls",
                ]
            },
            "FSE-05": {
                "category_name": "Field & Team Sports Gear",
                "items": [
                    "Hockey sticks",
                    "Cricket bats",
                    "Cricket balls",
                    "Baseball bats",
                    "Softballs",
                    "Lacrosse sticks",
                ]
            },
            "FTE-06": {
                "category_name": "Fitness & Training Equipment",
                "items": [
                    "Skipping ropes",
                    "Agility cones",
                    "Resistance bands",
                    "Medicine balls",
                    "Agility ladders",
                    "Speed hurdles",
                ]
            },
            "PSE-07": {
                "category_name": "Protective & Safety Gear",
                "items": [
                    "Shin guards",
                    "Helmets",
                    "Mouth guards",
                    "Knee pads",
                    "Elbow pads",
                    "Goalkeeper gloves",
                ]
            },
            "AWE-08": {
                "category_name": "Apparel & Wearables",
                "items": [
                    "Sports jerseys",
                    "Training bibs",
                    "Shorts",
                    "Socks",
                    "Tracksuits",
                    "Training vests",
                ]
            },
            "GLE-09": {
                "category_name": "Goalposts & Large Equipment",
                "items": [
                    "Football goalposts",
                    "Hockey goals",
                    "Netball posts",
                    "Portable goals",
                    "Rugby goalposts",
                ]
            },
            "ORE-10": {
                "category_name": "Outdoor & Recreational Equipment",
                "items": [
                    "Frisbees",
                    "Tug-of-war ropes",
                    "Camping tents",
                    "Recreation mats",
                    "Skipping hoops",
                ]
            },
            "WSE-11": {
                "category_name": "Water Sports Equipment",
                "items": [
                    "Life jackets",
                    "Swim kickboards",
                    "Swim fins",
                    "Goggles",
                    "Floating buoys",
                ]
            },
            "MSE-12": {
                "category_name": "Maintenance & Support Equipment",
                "items": [
                    "Ball pumps",
                    "Whistles",
                    "Stopwatches",
                    "First-aid kits",
                    "Repair kits",
                    "Equipment storage bags",
                ]
            },
        }
        
        serial_counter = 1000  # Start serial numbers from 1000
        added_count = 0
        
        for category_code, cat_data in equipment_data.items():
            category_name = cat_data["category_name"]
            
            for item_name in cat_data["items"]:
                # Check if equipment already exists
                existing = Equipment.query.filter_by(name=item_name, category_code=category_code).first()
                if existing:
                    print(f"  Skipping (exists): {item_name}")
                    continue
                
                # Generate unique serial number
                serial_number = f"SN-{serial_counter:06d}"
                serial_counter += 1
                
                # Create equipment record
                equipment = Equipment(
                    name=item_name,
                    category=category_name,
                    category_code=category_code,
                    quantity=0,  # Start with 0, will be distributed from warehouse
                    serial_number=serial_number,
                    is_active=True
                )
                
                db.session.add(equipment)
                print(f"Added: {category_code} - {item_name}")
                added_count += 1
        
        db.session.commit()
        
        print(f"\n✓ Equipment seeding completed!")
        print(f"  Total items added: {added_count}")
        print(f"  Total equipment in system: {Equipment.query.count()}")
        
    except Exception as e:
        db.session.rollback()
        print(f"✗ Error: {e}")
        raise
