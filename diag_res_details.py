import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db

app = create_app()

def diag():
    with app.app_context():
        print("Detailed diagnosis for Residential rows...")
        
        # Get count of RESIDENTIAL rows
        total_res = db.session.execute(text("SELECT count(*) FROM exposure_bmn_residential WHERE id LIKE 'RESIDENTIAL%'")).scalar()
        print(f"Total RESIDENTIAL: {total_res}")
        
        # Count where provinsi is already Bali
        res_bali = db.session.execute(text("SELECT count(*) FROM exposure_bmn_residential WHERE id LIKE 'RESIDENTIAL%' AND TRIM(UPPER(provinsi)) = 'BALI'")).scalar()
        print(f"RESIDENTIAL with provinsi=BALI: {res_bali}")
        
        # Count where kota is BALI
        res_kota_bali = db.session.execute(text("SELECT count(*) FROM exposure_bmn_residential WHERE id LIKE 'RESIDENTIAL%' AND TRIM(UPPER(kota)) = 'BALI'")).scalar()
        print(f"RESIDENTIAL with kota=BALI: {res_kota_bali}")
        
        # Sample rows where provinsi is NOT Bali
        print("\nSample rows where provinsi is NOT Bali:")
        rows = db.session.execute(text("SELECT id, nama_gedung, kota, provinsi FROM exposure_bmn_residential WHERE id LIKE 'RESIDENTIAL%' AND TRIM(UPPER(provinsi)) != 'BALI' LIMIT 10")).fetchall()
        for r in rows:
            print(f"ID: {r.id}, Name: {r.nama_gedung}, Kota: {r.kota}, Prov: {r.provinsi}")
            
        # Distinct values of Kota for non-Bali Residential
        print("\nDistinct Kota values for non-Bali Residential:")
        distinct_kota = db.session.execute(text("SELECT DISTINCT kota FROM exposure_bmn_residential WHERE id LIKE 'RESIDENTIAL%' AND TRIM(UPPER(provinsi)) != 'BALI'")).fetchall()
        print([k[0] for k in distinct_kota])

if __name__ == "__main__":
    diag()
