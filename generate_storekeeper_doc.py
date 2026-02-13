from app import create_app, db
from models import StoreKeeper, SatelliteCampus
import csv
from datetime import datetime

def generate_storekeeper_credentials_excel():
    """Generate a CSV file with all storekeeper credentials"""

    app = create_app()
    with app.app_context():
        print("Generating storekeeper credentials document...")

        # Get all storekeepers with campus info
        storekeepers = db.session.query(StoreKeeper, SatelliteCampus).join(
            SatelliteCampus, StoreKeeper.campus_id == SatelliteCampus.id
        ).order_by(StoreKeeper.payroll_number).all()

        # Save file
        filename = f"Storekeeper_Credentials_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['S.No', 'Campus Name', 'Storekeeper Name', 'Email Address', 'Payroll Number', 'Password']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header
            writer.writeheader()
            
            # Write data
            for idx, (storekeeper, campus) in enumerate(storekeepers, 1):
                writer.writerow({
                    'S.No': idx,
                    'Campus Name': campus.name,
                    'Storekeeper Name': storekeeper.full_name,
                    'Email Address': storekeeper.email,
                    'Payroll Number': storekeeper.payroll_number,
                    'Password': 'Password123'
                })

        print(f"\n✅ CSV Document generated successfully!")
        print(f"📄 File: {filename}")
        print(f"📊 Total Storekeepers: {len(storekeepers)}")
        print(f"\n✓ The document contains:")
        print("  - All storekeeper credentials")
        print("  - Login information for each storekeeper")
        print("  - Campus assignments")
        
        # Also create a text file with instructions
        txt_filename = f"Storekeeper_Instructions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(txt_filename, 'w', encoding='utf-8') as txtfile:
            txtfile.write("="*80 + "\n")
            txtfile.write("UNIVERSITY OF NAIROBI - SPORTS EQUIPMENT SYSTEM\n")
            txtfile.write("STOREKEEPER LOGIN CREDENTIALS & INSTRUCTIONS\n")
            txtfile.write("="*80 + "\n\n")
            txtfile.write(f"Generated on: {datetime.now().strftime('%B %d, %Y - %H:%M:%S')}\n\n")
            
            txtfile.write("STOREKEEPER CREDENTIALS\n")
            txtfile.write("-"*80 + "\n")
            txtfile.write(f"{'S.No':<5} {'Campus Name':<30} {'Storekeeper Name':<25} {'Email':<30}\n")
            txtfile.write("-"*80 + "\n")
            
            for idx, (storekeeper, campus) in enumerate(storekeepers, 1):
                txtfile.write(f"{idx:<5} {campus.name:<30} {storekeeper.full_name:<25} {storekeeper.email:<30}\n")
                txtfile.write(f"       Payroll: {storekeeper.payroll_number}  |  Password: Password123\n")
            
            txtfile.write("\n" + "="*80 + "\n")
            txtfile.write("LOGIN INSTRUCTIONS\n")
            txtfile.write("="*80 + "\n\n")
            txtfile.write("1. SYSTEM ACCESS\n")
            txtfile.write("   - Navigate to the Sports Equipment System login page\n")
            txtfile.write("   - Enter your Payroll Number in the username field\n")
            txtfile.write("   - Enter 'Password123' in the password field\n\n")
            
            txtfile.write("2. FIRST LOGIN\n")
            txtfile.write("   - After successful login, you may be prompted to change your password\n")
            txtfile.write("   - Update your password to a secure one immediately\n\n")
            
            txtfile.write("3. ACCOUNT DETAILS\n")
            txtfile.write("   - Name: Your assigned full name\n")
            txtfile.write("   - Campus: Your assigned campus location\n")
            txtfile.write("   - Email: Use this for system notifications and communication\n\n")
            
            txtfile.write("4. CAMPUS ASSIGNMENTS\n")
            for idx, (storekeeper, campus) in enumerate(storekeepers, 1):
                if idx == 1 or (storekeepers[idx-2][1].id != campus.id):
                    txtfile.write(f"   {campus.name}: Payroll {storekeeper.payroll_number}\n")
            
            txtfile.write("\n5. SUPPORT\n")
            txtfile.write("   - For login issues, contact the System Administrator\n")
            txtfile.write("   - For equipment-related questions, contact your Campus Manager\n")
        
        print(f"📄 Instructions File: {txt_filename}")
        print(f"\n✅ Both files have been generated successfully!")
        print(f"   - CSV file for importing into spreadsheets")
        print(f"   - Text file for easy reading and printing")

if __name__ == '__main__':
    generate_storekeeper_credentials_excel()