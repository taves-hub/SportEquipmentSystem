import os

class Config:
    SECRET_KEY = 'your-secret-key'
    # MySQL connection string
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/sports_equipment_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
