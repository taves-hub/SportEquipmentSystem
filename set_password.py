import psycopg2

try:
    # Try to connect without password first
    conn = psycopg2.connect(
        host='127.0.0.1',
        user='postgres',
        database='postgres'
    )
    conn.autocommit = True
    with conn.cursor() as cursor:
        cursor.execute("ALTER USER postgres PASSWORD 'Taves254';")
        print("Password set successfully")
    conn.close()
except Exception as e:
    print(f"Error: {e}")