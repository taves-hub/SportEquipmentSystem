from app import create_app
from models import IssuedEquipment

app = create_app()
with app.app_context():
    students = IssuedEquipment.query.filter(IssuedEquipment.student_id.like('CT202%')).all()
    for s in students:
        print(f'{s.student_id}: {s.student_name} - {s.student_email}')