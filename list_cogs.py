import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv('conversion/.env')

# Supabase Database Configuration
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

def list_raster_metadata():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cur = conn.cursor()
        cur.execute("SELECT filename, public_url FROM raster_metadata ORDER BY created_at DESC LIMIT 10;")
        rows = cur.fetchall()
        
        if not rows:
            print("No records found in raster_metadata table.")
        else:
            print("Daftar URL COG yang tersedia:")
            for row in rows:
                print(f"File: {row[0]}")
                print(f"URL: {row[1]}")
                print("-" * 30)
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_raster_metadata()
