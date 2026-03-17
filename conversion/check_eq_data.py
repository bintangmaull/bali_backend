import psycopg2
import os
from dotenv import load_dotenv
import rasterio

load_dotenv('conversion/.env')

def check_db():
    print("--- Database Check ---")
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute("SELECT public_url, filename FROM raster_metadata WHERE filename ILIKE '%earthquake%'")
    rows = cur.fetchall()
    for row in rows:
        print(f"URL: {row[0]}")
        print(f"File: {row[1]}")
    cur.close()
    conn.close()

def check_local_file():
    print("\n--- Local File Check (if exists) ---")
    path = "E:/Dashboard/Data/Hazard/DB/Earthquake/cog_earthquake_bali_PGA_500.tif"
    if os.path.exists(path):
        with rasterio.open(path) as src:
            print(f"Stats: min={src.read(1).min()}, max={src.read(1).max()}")
            print(f"CRS: {src.crs}")
            print(f"Bounds: {src.bounds}")
    else:
        print(f"File not found at: {path}")

if __name__ == "__main__":
    check_db()
    check_local_file()
