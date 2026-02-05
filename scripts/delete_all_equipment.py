# Script to delete all IssuedEquipment and Equipment records from the app database.
# Run from project root: python scripts/delete_all_equipment.py

import os
import sys

# Ensure project root is on sys.path so imports work when running as a script
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from extensions import db
from models import Equipment, IssuedEquipment


app = create_app()
with app.app_context():
    try:
        total_issued = IssuedEquipment.query.count()
        total_equipment = Equipment.query.count()
        print(f"Existing IssuedEquipment: {total_issued}")
        print(f"Existing Equipment: {total_equipment}")

        # Delete issued equipment first (to avoid FK constraint issues)
        deleted_issued = db.session.query(IssuedEquipment).delete(synchronize_session=False)
        print(f"Deleted IssuedEquipment rows: {deleted_issued}")

        # Then delete equipment
        deleted_equipment = db.session.query(Equipment).delete(synchronize_session=False)
        print(f"Deleted Equipment rows: {deleted_equipment}")

        db.session.commit()

        print("Deletion committed.")
        print(f"Remaining IssuedEquipment: {IssuedEquipment.query.count()}")
        print(f"Remaining Equipment: {Equipment.query.count()}")
    except Exception as e:
        db.session.rollback()
        print("Error during deletion:", e)
        raise
