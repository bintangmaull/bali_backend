import sys
import os
import csv

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from sqlalchemy import text
from app import create_app
from app.extensions import db

app = create_app()

CSV_PATH = r"E:\Dashboard\Data\Exposure\exposure_bmnresfix.csv"

sql_create_table = """
CREATE TABLE IF NOT EXISTS exposure_bmn_residential (
    id VARCHAR(50) PRIMARY KEY,
    lon DOUBLE PRECISION NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    taxonomy VARCHAR(100),
    jumlah_lantai INTEGER,
    nama_gedung VARCHAR(255),
    luas DOUBLE PRECISION,
    nilai_aset DOUBLE PRECISION,
    kota VARCHAR(255),
    provinsi VARCHAR(255),
    geom GEOMETRY(POINT, 4326)
);

CREATE INDEX IF NOT EXISTS idx_exposure_bmn_res_geom ON exposure_bmn_residential USING GIST (geom);
"""

def run_migration():
    with app.app_context():
        # 1. Create table
        try:
            db.session.execute(text(sql_create_table))
            db.session.commit()
            print("Table check/creation successful.")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating table: {e}")
            return

        # 2. Read and Insert data from CSV
        if not os.path.exists(CSV_PATH):
            print(f"Error: CSV file not found at {CSV_PATH}")
            return

        print(f"Reading data from {CSV_PATH}...")
        
        try:
            with open(CSV_PATH, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                count = 0
                for row in reader:
                    # Map CSV columns to table columns
                    # id;lon;lat;taxonomy;jumlah_lantai;nama_gedung;luas;nilai_aset;kota;prov
                    
                    data = {
                        "id": row["id"],
                        "lon": float(row["lon"]) if row["lon"] else 0,
                        "lat": float(row["lat"]) if row["lat"] else 0,
                        "tax": row["taxonomy"],
                        "floors": int(row["jumlah_lantai"]) if row["jumlah_lantai"] else None,
                        "name": row["nama_gedung"],
                        "luas": float(row["luas"]) if row["luas"] else None,
                        "asset": float(row["nilai_aset"]) if row["nilai_aset"] else None,
                        "city": row["kota"],
                        "prov": row["prov"],
                    }

                    sql_insert = text("""
                        INSERT INTO exposure_bmn_residential (id, lon, lat, taxonomy, jumlah_lantai, nama_gedung, luas, nilai_aset, kota, provinsi, geom)
                        VALUES (:id, :lon, :lat, :tax, :floors, :name, :luas, :asset, :city, :prov, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                        ON CONFLICT (id) DO UPDATE SET
                            lon = EXCLUDED.lon,
                            lat = EXCLUDED.lat,
                            taxonomy = EXCLUDED.taxonomy,
                            jumlah_lantai = EXCLUDED.jumlah_lantai,
                            nama_gedung = EXCLUDED.nama_gedung,
                            luas = EXCLUDED.luas,
                            nilai_aset = EXCLUDED.nilai_aset,
                            kota = EXCLUDED.kota,
                            provinsi = EXCLUDED.provinsi,
                            geom = EXCLUDED.geom;
                    """)
                    
                    db.session.execute(sql_insert, data)
                    count += 1
                    if count % 100 == 0:
                        db.session.commit()
                        print(f"Processed {count} rows...")
                
                db.session.commit()
                print(f"Successfully processed total {count} rows.")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error during data import: {e}")

if __name__ == "__main__":
    run_migration()
