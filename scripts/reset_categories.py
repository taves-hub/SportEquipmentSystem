"""Reset equipment categories and seed with actual sports equipment categories."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from extensions import db
from models import EquipmentCategory

app = create_app()
with app.app_context():
    try:
        # Delete existing categories
        deleted = EquipmentCategory.query.delete(synchronize_session=False)
        print(f"Deleted {deleted} existing categories")
        
        # Add new sports equipment categories
        categories = [
            EquipmentCategory(category_code="BSE-01", category_name="Ball Sports Equipment", description="Basketballs, footballs, volleyballs, soccer balls, etc."),
            EquipmentCategory(category_code="NCE-02", category_name="Net & Court Equipment", description="Nets, court markers, badminton equipment, etc."),
            EquipmentCategory(category_code="ATE-03", category_name="Athletics & Track Equipment", description="Hurdles, starting blocks, javelins, shot puts, etc."),
            EquipmentCategory(category_code="ISE-04", category_name="Indoor Sports Equipment", description="Table tennis, badminton, indoor games equipment"),
            EquipmentCategory(category_code="FSE-05", category_name="Field & Team Sports Gear", description="Team uniforms, field equipment, team sports gear"),
            EquipmentCategory(category_code="FTE-06", category_name="Fitness & Training Equipment", description="Dumbbells, weights, resistance bands, training mats"),
            EquipmentCategory(category_code="PSE-07", category_name="Protective & Safety Gear", description="Helmets, pads, protective equipment, safety gear"),
            EquipmentCategory(category_code="AWE-08", category_name="Apparel & Wearables", description="Sports clothing, shoes, wristbands, athletic wear"),
            EquipmentCategory(category_code="GLE-09", category_name="Goalposts & Large Equipment", description="Goalposts, standards, large fixed equipment"),
            EquipmentCategory(category_code="ORE-10", category_name="Outdoor & Recreational Equipment", description="Camping, hiking, outdoor recreation gear"),
            EquipmentCategory(category_code="WSE-11", category_name="Water Sports Equipment", description="Swimming equipment, water polo, diving gear"),
            EquipmentCategory(category_code="MSE-12", category_name="Maintenance & Support Equipment", description="Repair tools, maintenance equipment, support gear"),
        ]
        
        for cat in categories:
            db.session.add(cat)
            print(f"Added category: {cat.category_code} - {cat.category_name}")
        
        db.session.commit()
        print("\nCategories reset successfully!")
        print(f"Total categories: {EquipmentCategory.query.count()}")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        raise
