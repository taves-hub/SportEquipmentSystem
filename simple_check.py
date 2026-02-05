from app import create_app
from models import Student, Staff

print("Starting database check...")

try:
    app = create_app()
    print("App created successfully")

    with app.app_context():
        print("App context entered")

        # Try to query the tables
        student_count = Student.query.count()
        staff_count = Staff.query.count()

        print(f"Database check successful!")
        print(f"Students: {student_count}")
        print(f"Staff: {staff_count}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()