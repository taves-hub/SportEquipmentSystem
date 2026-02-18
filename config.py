import os


class Config:
    SECRET_KEY = 'your-secret-key'
    # PostgreSQL connection string
    SQLALCHEMY_DATABASE_URI = 'postgresql://sport_equipment_db_user:tTPNuwy5mB9wmGVbZU5kOVYD3A6SCNbJ@dpg-d67e0mbnv86c739mctug-a:5432/sport_equipment_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
