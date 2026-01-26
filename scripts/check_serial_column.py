import sys
import os
import pymysql
import urllib.parse
# Ensure project root is on sys.path so `config` can be imported when running from scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

uri = Config.SQLALCHEMY_DATABASE_URI
if uri.startswith('mysql+pymysql://'):
    uri = uri.replace('mysql+pymysql://', '')
parsed = urllib.parse.urlparse('//' + uri)
user = parsed.username or 'root'
password = parsed.password or ''
host = parsed.hostname or 'localhost'
db = parsed.path.lstrip('/')

print(f'Connecting to {host}/{db} as {user}')
try:
    conn = pymysql.connect(host=host, user=user, password=password, database=db)
    cur = conn.cursor()
    cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='equipment'", (db,))
    cols = [r[0] for r in cur.fetchall()]
    print('Columns in equipment:', cols)
    if 'serial_number' in cols:
        print('RESULT: serial_number column EXISTS')
    else:
        print('RESULT: serial_number column MISSING')
    cur.close()
    conn.close()
except Exception as e:
    print('ERROR connecting or querying DB:', e)
