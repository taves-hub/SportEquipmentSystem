import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config
import pymysql
import urllib.parse

uri = Config.SQLALCHEMY_DATABASE_URI
if uri.startswith('mysql+pymysql://'):
    uri = uri.replace('mysql+pymysql://', '')
parsed = urllib.parse.urlparse('//' + uri)
user = parsed.username or 'root'
password = parsed.password or ''
host = parsed.hostname or 'localhost'
db = parsed.path.lstrip('/')

conn = pymysql.connect(host=host, user=user, password=password, database=db)
cur = conn.cursor()
cur.execute("SELECT INDEX_NAME, NON_UNIQUE, COLUMN_NAME FROM INFORMATION_SCHEMA.STATISTICS WHERE TABLE_SCHEMA=%s AND TABLE_NAME='equipment' ORDER BY INDEX_NAME, SEQ_IN_INDEX", (db,))
rows = cur.fetchall()
print('Indexes for equipment:')
for r in rows:
    print(r)
cur.close()
conn.close()