import os
from datetime import timedelta
from urllib.parse import quote_plus

class Config:
    """Konfigurasi Flask untuk Supabase"""

    DB_USER = os.getenv('DB_USER', 'postgres.btwsqklqtqgrlmvysgsc')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '@Guyengan123')
    DB_HOST = os.getenv('DB_HOST', 'aws-1-ap-northeast-1.pooler.supabase.com')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'postgres')

    # URL Encoding password agar karakter spesial (@, :, /, dll) aman digunakan
    safe_password = quote_plus(DB_PASSWORD)

    # Konfigurasi URI dengan SSL mode
    if DB_PASSWORD:
        SQLALCHEMY_DATABASE_URI = (
            f'postgresql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require'
        )
    else:
        SQLALCHEMY_DATABASE_URI = (
            f'postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require'
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))

    DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't']

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'cardinal-aal-super-secret-key-2024')
    # Token expires in 7 days — MUST be timedelta, not raw int
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)