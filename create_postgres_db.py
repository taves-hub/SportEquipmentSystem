import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_postgres_database():
    try:
        # Connect to PostgreSQL server (default database)
        connection = psycopg2.connect(
            host='127.0.0.1',
            user='postgres',  # Change this to your PostgreSQL username
            password='Taves254',  # Change this to your PostgreSQL password
            database='postgres'
        )
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'sports_equipment_db'")
            exists = cursor.fetchone()

            if not exists:
                cursor.execute("CREATE DATABASE sports_equipment_db")
                print("✓ Database 'sports_equipment_db' created")
            else:
                print("✓ Database 'sports_equipment_db' already exists")

            # Create user and grant permissions (optional)
            try:
                cursor.execute("CREATE USER sports_user WITH PASSWORD 'sports_password'")
                cursor.execute("GRANT ALL PRIVILEGES ON DATABASE sports_equipment_db TO sports_user")
                print("✓ Database user created and permissions granted")
            except psycopg2.errors.DuplicateObject:
                print("✓ Database user already exists")

        connection.close()
        print("✓ PostgreSQL connection closed")

    except Exception as e:
        print("✕ Error:", str(e))

if __name__ == '__main__':
    create_postgres_database()