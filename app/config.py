import os
from datetime import timedelta
from urllib.parse import quote_plus

class Config:
    """Konfigurasi Flask untuk Supabase"""



    DB_USER = os.getenv('DB_USER', 'aal-db')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '@Guyengan123')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'aal-db')

    # URL Encoding password agar karakter spesial (@, :, /, dll) aman digunakan
    safe_password = quote_plus(DB_PASSWORD)

    # Base URI Database
    if DB_PASSWORD:
        SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    else:
        SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    # Tambahkan sslmode=require HANYA jika host-nya adalah Supabase (Cloud)
    # Jika menggunakan VPS sendiri (Dokploy), tidak perlu SSL karena jalurnya internal Docker
    if "supabase" in DB_HOST.lower():
        SQLALCHEMY_DATABASE_URI += "?sslmode=require"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Konfigurasi Pool SQLAlchemy untuk Supabase PgBouncer (Transaction Mode)
    # Ini mencegah error "server closed the connection unexpectedly"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,        # Cek koneksi sebelum digunakan (menghindari error server closed)
        "pool_recycle": 300,          # Recycle koneksi setiap 5 menit sebelum Supabase mematikannya
        "pool_timeout": 30,           # Waktu tunggu maksimal untuk mendapatkan koneksi dari pool (detik)
        "pool_size": 10,              # Jumlah koneksi permanen di pool
        "max_overflow": 15            # Ekstra koneksi jika pool penuh
    }

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))

    DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 't']

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'cardinal-aal-super-secret-key-2024')
    # Token expires in 7 days — MUST be timedelta, not raw int
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)