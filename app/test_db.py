from sqlalchemy import create_engine, text
from config import Config

def test_connection():
    try:
        # Membuat engine dari konfigurasi Anda
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        # Mencoba membuka koneksi
        with engine.connect() as connection:
            # Menjalankan query sederhana
            result = connection.execute(text("SELECT 1"))
            print("✅ Koneksi Berhasil!")
            print(f"Hasil Query: {result.scalar()}")
            
    except Exception as e:
        print("❌ Koneksi Gagal!")
        print(f"Error detail: {e}")

if __name__ == "__main__":
    test_connection()