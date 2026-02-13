import os

class Config:
    SECRET_KEY = 'your-secret-key'
    # PostgreSQL connection string
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:Taves254@localhost/sports_equipment_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
