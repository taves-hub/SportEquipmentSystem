# MySQL to PostgreSQL Migration Guide
# ===================================

"""
Complete step-by-step guide to migrate Sports Equipment System from MySQL to PostgreSQL

PREREQUISITES:
1. Install PostgreSQL on your system
2. Create a PostgreSQL user and database
3. Backup your MySQL data (recommended)

STEPS:
1. Install dependencies
2. Configure PostgreSQL connection
3. Create PostgreSQL database
4. Initialize PostgreSQL schema
5. Migrate data from MySQL
6. Update application configuration
7. Test the migration

Run these commands in order:
"""

# Step 1: Install PostgreSQL driver
print("Step 1: Installing PostgreSQL dependencies...")
print("pip install psycopg2-binary")

# Step 2: Update configuration
print("\nStep 2: Update config.py with PostgreSQL connection string")
print("Example: postgresql://username:password@localhost/sports_equipment_db")

# Step 3: Create PostgreSQL database
print("\nStep 3: Create PostgreSQL database")
print("python create_postgres_db.py")

# Step 4: Initialize schema
print("\nStep 4: Initialize PostgreSQL schema")
print("python init_postgres_db.py")

# Step 5: Migrate data
print("\nStep 5: Migrate data from MySQL to PostgreSQL")
print("python migrate_mysql_to_postgres.py")

# Step 6: Update Flask-Migrate
print("\nStep 6: Update Flask-Migrate for PostgreSQL")
print("flask db init  # If not already done")
print("flask db migrate -m 'Migrate to PostgreSQL'")
print("flask db upgrade")

# Step 7: Test
print("\nStep 7: Test the application")
print("python app.py")

print("\n" + "="*50)
print("IMPORTANT NOTES:")
print("- Update the database URI in config.py with your actual PostgreSQL credentials")
print("- Make sure PostgreSQL is running and accessible")
print("- Test thoroughly after migration")
print("- Consider keeping MySQL as backup until migration is verified")
print("="*50)