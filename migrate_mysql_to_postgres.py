import pymysql
import psycopg2
import json
from datetime import datetime

# MySQL connection
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'sports_equipment_db'
}

# PostgreSQL connection
POSTGRES_CONFIG = {
    'host': '127.0.0.1',
    'user': 'postgres',  # Change this to your PostgreSQL username
    'password': 'Taves254',  # Change this to your PostgreSQL password
    'database': 'sports_equipment_db'
}

def migrate_table(table_name, mysql_cursor, postgres_cursor, column_mappings=None):
    """Migrate data from MySQL table to PostgreSQL table"""
    print(f"Migrating table: {table_name}")

    # Get MySQL data
    mysql_cursor.execute(f"SELECT * FROM {table_name}")
    rows = mysql_cursor.fetchall()

    if not rows:
        print(f"  No data in {table_name}")
        return

    # Get column names
    mysql_cursor.execute(f"DESCRIBE {table_name}")
    columns = [col[0] for col in mysql_cursor.fetchall()]

    # Apply column mapping if provided
    if column_mappings and table_name in column_mappings:
        columns = [column_mappings[table_name].get(col, col) for col in columns]

    # Prepare PostgreSQL insert
    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)

    # Handle special cases for data conversion
    converted_rows = []
    for row in rows:
        converted_row = []
        for i, value in enumerate(row):
            if isinstance(value, datetime):
                # PostgreSQL handles datetime differently
                converted_row.append(value)
            elif isinstance(value, str) and value.startswith('0000-00-00'):
                # Handle invalid MySQL dates
                converted_row.append(None)
            elif table_name in ['notifications', 'satellite_campuses', 'equipment_categories', 'storekeepers', 'equipment'] and columns[i] == 'is_active':
                # Convert integer to boolean for is_active column
                converted_row.append(bool(value))
            elif table_name == 'storekeepers' and columns[i] == 'is_approved':
                # Convert integer to boolean for is_approved column
                converted_row.append(bool(value))
            elif table_name == 'issued_equipment' and columns[i] == 'student_name':
                # Skip student_name column as it doesn't exist in PostgreSQL
                continue
            else:
                converted_row.append(value)
        
        # Skip rows where student_name was removed
        if table_name == 'issued_equipment' and len(converted_row) != len([col for col in columns if col != 'student_name']):
            continue
            
        converted_rows.append(tuple(converted_row))

    # Adjust columns list if we removed student_name
    if table_name == 'issued_equipment':
        columns = [col for col in columns if col != 'student_name']

    # Insert data
    try:
        # Use INSERT ... ON CONFLICT DO NOTHING to skip duplicates
        conflict_columns = {
            'admins': 'id',
            'students': 'id', 
            'staff': 'payroll_number',
            'clearance': 'id',
            'satellite_campuses': 'id',
            'equipment_categories': 'id',
            'storekeepers': 'id',
            'equipment': 'id',
            'issued_equipment': 'id',
            'campus_distributions': 'id',
            'notifications': 'id'
        }
        
        if table_name in conflict_columns:
            conflict_col = conflict_columns[table_name]
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders}) ON CONFLICT ({conflict_col}) DO NOTHING"
        else:
            insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        postgres_cursor.executemany(insert_sql, converted_rows)
        print(f"  ✓ Migrated {len(rows)} rows")
    except Exception as e:
        print(f"  ✕ Error migrating {table_name}: {e}")
        # Try individual inserts for debugging
        for i, row in enumerate(converted_rows):
            try:
                postgres_cursor.execute(
                    f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                    row
                )
            except Exception as e2:
                print(f"    Row {i} failed: {e2} - Data: {row}")

def main():
    mysql_conn = None
    postgres_conn = None

    try:
        # Connect to MySQL
        print("Connecting to MySQL...")
        mysql_conn = pymysql.connect(**MYSQL_CONFIG)
        mysql_cursor = mysql_conn.cursor()

        # Connect to PostgreSQL
        print("Connecting to PostgreSQL...")
        postgres_conn = psycopg2.connect(**POSTGRES_CONFIG)
        postgres_cursor = postgres_conn.cursor()

        # Tables to migrate (in order to handle foreign keys)
        tables = [
            'satellite_campuses',
            'equipment_categories',
            'admins',
            'storekeepers',
            'students',
            'staff',
            'equipment',
            'issued_equipment',
            'campus_distributions',
            'clearance',
            'notifications'
        ]

        # Column mappings if needed (MySQL to PostgreSQL naming differences)
        column_mappings = {
            # Add any column name mappings here if needed
        }

        # Migrate each table
        for table in tables:
            try:
                migrate_table(table, mysql_cursor, postgres_cursor, column_mappings)
                postgres_conn.commit()
            except Exception as e:
                print(f"✕ Failed to migrate {table}: {e}")
                postgres_conn.rollback()

        print("\n✓ Migration completed!")

    except Exception as e:
        print(f"✕ Migration failed: {e}")
    finally:
        if mysql_conn:
            mysql_conn.close()
        if postgres_conn:
            postgres_conn.close()

if __name__ == '__main__':
    main()