import pymysql

def create_database():
    try:
        # Connect to MySQL server
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password=''
        )
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute("CREATE DATABASE IF NOT EXISTS sports_equipment_db")
            print("✓ Database 'sports_equipment_db' created or already exists")
            
            # Use the database
            cursor.execute("USE sports_equipment_db")
            
            # Show tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            if tables:
                print("Existing tables:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("No tables exist yet")
                
        connection.close()
        print("✓ Database connection closed")
        
    except Exception as e:
        print("✕ Error:", str(e))

if __name__ == '__main__':
    create_database()