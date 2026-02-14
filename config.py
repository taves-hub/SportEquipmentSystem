import os

class Config:
    SECRET_KEY = 'your-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        SQLALCHEMY_DATABASE_URI = 'postgresql://sport_equipment_db_user:tTPNuwy5mB9wmGVbZU5kOVYD3A6SCNbJ@dpg-d67e0mbnv86c739mctug-a:5432/sport_equipment_db'
    )
