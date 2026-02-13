# config.py
import os

class Config:
    # Use environment variables for security
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://localhost/sport_equipment_db'  # fallback for local dev
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
