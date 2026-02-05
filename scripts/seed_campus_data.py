"""Seed satellite campuses and equipment categories for testing campus distribution."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from extensions import db
from models import SatelliteCampus, EquipmentCategory

app = create_app()
with app.app_context():
    try:
        # Sample satellite campuses
        campuses = [
            SatelliteCampus(name="Main Campus", code="MAIN", location="Main Campus"),
            SatelliteCampus(name="Lower Kabete Campus", code="LK", location="Lower Kabete"),
            SatelliteCampus(name="Kikuyu Campus", code="KK", location="Kikuyu"),
            SatelliteCampus(name="Parklands Campus", code="PL", location="Parklands"),
            SatelliteCampus(name="Kenya Science Campus", code="KSC", location="Kenya Science"),
            SatelliteCampus(name="Mombasa Campus", code="MB", location="Mombasa"),
            SatelliteCampus(name="Kisumu Campus", code="KM", location="Kisumu"),
        ]
        
        for campus in campuses:
            existing = SatelliteCampus.query.filter_by(code=campus.code).first()
            if not existing:
                db.session.add(campus)
                print(f"Added campus: {campus.name}")
            else:
                print(f"Campus {campus.name} already exists, skipping.")
        
        # Sample equipment categories
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
            existing = EquipmentCategory.query.filter_by(category_code=cat.category_code).first()
            if not existing:
                db.session.add(cat)
                print(f"Added category: {cat.category_code} - {cat.category_name}")
            else:
                print(f"Category {cat.category_code} already exists, skipping.")
        
        db.session.commit()
        print("\nSeed data committed successfully!")
        print(f"Total campuses: {SatelliteCampus.query.count()}")
        print(f"Total categories: {EquipmentCategory.query.count()}")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        raise
