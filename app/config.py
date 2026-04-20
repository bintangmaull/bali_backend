import os
from datetime import timedelta
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables dari file .env di root folder
load_dotenv()

class Config:
    """Konfigurasi Flask untuk VPS Database"""

    # Mengambil dari environment variable, dengan default ke VPS detail
    DB_USER = os.getenv('DB_USER', 'aal-db')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '123456')
    DB_HOST = os.getenv('DB_HOST', '72.60.76.178')
    DB_PORT = os.getenv('DB_PORT', '5433')
    DB_NAME = os.getenv('DB_NAME', 'aal_db')

    # URL Encoding password agar karakter spesial aman digunakan
    safe_password = quote_plus(DB_PASSWORD)

    # Base URI Database
    SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Konfigurasi Pool SQLAlchemy yang optimal untuk VPS
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
        "pool_timeout": 30,
        "pool_size": 20,
        "max_overflow": 10
    }

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))

    DEBUG = os.getenv('DEBUG', 'True').lower() in ['true', '1', 't']

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'D3ployment2026!AAL')
    # Token expires in 7 days
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)