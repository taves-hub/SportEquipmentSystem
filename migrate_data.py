from app import create_app
from models import Student, Staff, IssuedEquipment, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Starting data migration to remove redundancy...")

    # Migrate student data using raw SQL to access old columns
    student_data = db.session.execute(text("""
        SELECT DISTINCT student_id, student_name, student_email, student_phone
        FROM issued_equipment
        WHERE student_id IS NOT NULL AND student_id != ''
        ORDER BY student_id
    """)).fetchall()

    migrated_students = 0
    for row in student_data:
        student_id, student_name, student_email, student_phone = row
        
        # Check if student already exists
        existing_student = Student.query.get(student_id)
        if not existing_student:
            if student_name and student_email:  # Only create if we have required data
                student = Student(
                    id=student_id,
                    name=student_name,
                    email=student_email,
                    phone=student_phone or None
                )
                db.session.add(student)
                migrated_students += 1
                print(f"Created student: {student_id} - {student_name}")

    print(f"Total students migrated: {migrated_students}")

    # Migrate staff data using raw SQL to access old columns
    staff_data = db.session.execute(text("""
        SELECT DISTINCT staff_payroll, staff_name, staff_email
        FROM issued_equipment
        WHERE staff_payroll IS NOT NULL AND staff_payroll != ''
        ORDER BY staff_payroll
    """)).fetchall()

    migrated_staff = 0
    for row in staff_data:
        staff_payroll, staff_name, staff_email = row
        
        # Check if staff already exists
        existing_staff = Staff.query.get(staff_payroll)
        if not existing_staff:
            if staff_name and staff_email:  # Only create if we have required data
                staff = Staff(
                    payroll_number=staff_payroll,
                    name=staff_name,
                    email=staff_email
                )
                db.session.add(staff)
                migrated_staff += 1
                print(f"Created staff: {staff_payroll} - {staff_name}")

    print(f"Total staff migrated: {migrated_staff}")

    # Commit all changes
    try:
        db.session.commit()
        print("Data migration completed successfully!")
        print(f"Created {migrated_students} students and {migrated_staff} staff records.")
    except Exception as e:
        db.session.rollback()
        print(f"Error during migration: {e}")
        raise