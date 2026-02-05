from app import create_app
from models import Student, Staff, IssuedEquipment
import sys

try:
    app = create_app()
    with app.app_context():
        print("Database connection successful!")
        student_count = Student.query.count()
        staff_count = Staff.query.count()
        issued_count = IssuedEquipment.query.count()

        print(f"Students: {student_count}")
        print(f"Staff: {staff_count}")
        print(f"Issued Equipment: {issued_count}")

        # Show some sample data
        if student_count > 0:
            students = Student.query.limit(3).all()
            print("\nSample Students:")
            for s in students:
                print(f"  {s.id}: {s.name} - {s.email}")

        if staff_count > 0:
            staff = Staff.query.limit(3).all()
            print("\nSample Staff:")
            for s in staff:
                print(f"  {s.payroll_number}: {s.name} - {s.email}")

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)