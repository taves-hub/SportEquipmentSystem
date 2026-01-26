import pymysql
from config import Config

def test_database_connection():
    try:
        # Parse the SQLAlchemy URI to get connection details
        uri = Config.SQLALCHEMY_DATABASE_URI
        uri = uri.replace('mysql+pymysql://', '')
        credentials, host_db = uri.split('@')
        username, password = credentials.split(':')
        host, database = host_db.split('/')

        # Create connection
        connection = pymysql.connect(
            host=host,
            user=username,
            password=password if password else '',
            database=database
        )
        
        print("✓ Successfully connected to MySQL server")
        
        # Check if database exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE()")
            db_name = cursor.fetchone()[0]
            print(f"✓ Current database: {db_name}")
            
            # Get table list
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            if tables:
                print("✓ Existing tables:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("! No tables found in the database")
                
        connection.close()
        print("✓ Connection closed successfully")
        
    except pymysql.Error as e:
        print("❌ Database connection failed!")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_database_connection()