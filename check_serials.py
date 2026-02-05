from app import create_app
from models import IssuedEquipment

app = create_app()
app.app_context().push()

issues_with_serials = IssuedEquipment.query.filter(IssuedEquipment.serial_numbers.isnot(None)).all()
print(f'Issues with serial numbers: {len(issues_with_serials)}')

for issue in issues_with_serials[:5]:
    print(f'ID: {issue.id}, Serials: {issue.serial_numbers}, Status: {issue.status}, Student: {issue.student_id}, Staff: {issue.staff_payroll}')

# Also check total issued equipment
total_issued = IssuedEquipment.query.filter_by(status='Issued').count()
print(f'Total issued equipment: {total_issued}')

# Check if any of the serial number items are still issued
issued_with_serials = IssuedEquipment.query.filter(
    IssuedEquipment.serial_numbers.isnot(None),
    IssuedEquipment.status == 'Issued'
).all()
print(f'Issued items with serial numbers: {len(issued_with_serials)}')

for issue in issued_with_serials:
    print(f'Issued ID: {issue.id}, Serials: {issue.serial_numbers}, Student: {issue.student_id}, Staff: {issue.staff_payroll}')