from app import app
from models import StoreKeeper, AccessLog
from extensions import db

with app.app_context():
    print("=== STOREKEEPERS ===")
    storekeepers = StoreKeeper.query.all()
    print(f"Total storekeepers: {len(storekeepers)}")
    for sk in storekeepers:
        print(f"  ID: {sk.id}, Payroll: {sk.payroll_number}, Name: {sk.full_name}, Approved: {sk.is_approved}")

    print("\n=== STOREKEEPER ACCESS LOGS ===")
    logs = AccessLog.query.filter_by(user_type='storekeeper').order_by(AccessLog.timestamp.desc()).limit(10).all()
    print(f"Total storekeeper logs: {len(logs)}")
    for log in logs:
        print(f"  {log.timestamp} - {log.username} -> {log.endpoint} ({log.method})")

    print("\n=== ALL ACCESS LOGS (Last 10) ===")
    all_logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(10).all()
    for log in all_logs:
        print(f"  {log.timestamp} - {log.user_type}: {log.username} -> {log.endpoint}")

    print("\n=== CHECKING LOGGING CODE ===")
    # Check if the logging code is working by looking at recent requests
    print("Checking if storekeeper routes are being accessed...")