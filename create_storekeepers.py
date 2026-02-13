import random
import string
from datetime import datetime
from werkzeug.security import generate_password_hash
from app import create_app, db
from models import StoreKeeper, SatelliteCampus

def generate_random_name():
    """Generate a random Kenyan name"""
    first_names = [
        'John', 'Mary', 'Peter', 'Sarah', 'David', 'Grace', 'Michael', 'Ann',
        'James', 'Elizabeth', 'Paul', 'Margaret', 'Joseph', 'Catherine', 'Thomas',
        'Rose', 'Daniel', 'Jane', 'Samuel', 'Lucy', 'Simon', 'Joyce', 'Philip',
        'Susan', 'Stephen', 'Rebecca', 'Francis', 'Florence', 'Anthony', 'Alice',
        'Robert', 'Beatrice', 'Charles', 'Eunice', 'Henry', 'Gladys', 'Isaac',
        'Helen', 'Jacob', 'Irene', 'Kennedy', 'Mercy', 'Lawrence', 'Naomi',
        'Martin', 'Priscilla', 'Nicholas', 'Rachel', 'Oscar', 'Sylvia'
    ]

    last_names = [
        'Mwangi', 'Wanjiku', 'Kiprop', 'Cherono', 'Oduya', 'Achieng', 'Ochieng',
        'Njoroge', 'Wairimu', 'Kiptoo', 'Chebet', 'Rono', 'Langat', 'Rotich',
        'Koech', 'Bett', 'Sigei', 'Kemboi', 'Tanui', 'Cheruiyot', 'Kipkemboi',
        'Kiplagat', 'Kiprop', 'Chepkorir', 'Jeptoo', 'Kiptanui', 'Koskei',
        'Mitei', 'Mburu', 'Kamau', 'Njeri', 'Wanjohi', 'Maina', 'Githinji',
        'Muthoni', 'Wambui', 'Nyambura', 'Wangari', 'Mumbi', 'Kahiga'
    ]

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    return f"{first_name} {last_name}"

# Global payroll counter starting from 100200
payroll_counter = 100200

def generate_payroll_number():
    """Generate a unique sequential payroll number"""
    global payroll_counter
    current = str(payroll_counter)
    payroll_counter += 1
    return current

def generate_password():
    """Generate a simple password (similar format)"""
    # Generate a password with just letters and numbers
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=10))

def generate_email(first_name, last_name):
    """Generate email as first letter + last name + @uonbi.ac.ke"""
    return f"{first_name[0].lower()}{last_name.lower()}@uonbi.ac.ke"

def create_storekeepers():
    """Create random storekeepers for each campus"""

    app = create_app()
    with app.app_context():
        print("Creating random storekeepers for each campus...")

        # Get all campuses
        campuses = SatelliteCampus.query.all()

        storekeepers_created = []
        credentials = []

        for campus in campuses:
            # Create 2-4 storekeepers per campus
            num_storekeepers = random.randint(2, 4)

            for i in range(num_storekeepers):
                # Generate random data
                full_name = generate_random_name()
                first_name, last_name = full_name.split()
                payroll_number = generate_payroll_number()
                password = generate_password()
                email = generate_email(first_name, last_name)

                # Check if storekeeper already exists
                existing = StoreKeeper.query.filter_by(payroll_number=payroll_number).first()
                if not existing:
                    # Hash the password
                    password_hash = generate_password_hash(password)

                    # Create storekeeper
                    storekeeper = StoreKeeper(
                        payroll_number=payroll_number,
                        full_name=full_name,
                        email=email,
                        password_hash=password_hash,
                        campus_id=campus.id,
                        is_approved=True,
                        approved_at=datetime.utcnow(),
                        created_at=datetime.utcnow()
                    )

                    db.session.add(storekeeper)
                    storekeepers_created.append(storekeeper)

                    # Store credentials for display
                    credentials.append({
                        'campus': campus.name,
                        'name': full_name,
                        'payroll': payroll_number,
                        'email': email,
                        'password': password
                    })

                    print(f"✓ Created: {full_name} ({payroll_number}) - {campus.name}")

        db.session.commit()
        print(f"\n✅ Successfully created {len(storekeepers_created)} storekeepers")

        # Display credentials
        print("\n" + "="*80)
        print("STOREKEEPER CREDENTIALS")
        print("="*80)

        for cred in credentials:
            print(f"\nCampus: {cred['campus']}")
            print(f"Name: {cred['name']}")
            print(f"Payroll Number: {cred['payroll']}")
            print(f"Email: {cred['email']}")
            print(f"Password: {cred['password']}")
            print("-" * 40)

        print(f"\n📋 Total Storekeepers Created: {len(credentials)}")
        print("All storekeepers are approved and ready to use the system!")

if __name__ == '__main__':
    create_storekeepers()