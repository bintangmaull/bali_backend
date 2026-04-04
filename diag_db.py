import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db

app = create_app()

def check_db():
    with app.app_context():
        print("Checking exposure_bmn_residential table...")
        
        # Check counts
        total = db.session.execute(text("SELECT count(*) FROM exposure_bmn_residential")).scalar()
        bali_count = db.session.execute(text("SELECT count(*) FROM exposure_bmn_residential WHERE TRIM(LOWER(provinsi)) = 'bali'")).scalar()
        
        print(f"Total rows: {total}")
        print(f"Rows with provinsi='bali': {bali_count}")
        
        # Check first 5 rows for Bali
        rows = db.session.execute(text("SELECT id, nama_gedung, kota, provinsi FROM exposure_bmn_residential WHERE TRIM(LOWER(provinsi)) = 'bali' LIMIT 10")).fetchall()
        for r in rows:
            print(f"ID: {r.id}, Name: {r.nama_gedung}, City: {r.kota}, Prov: {r.provinsi}")
            
        # specifically check for RESIDENTIAL
        res_count = db.session.execute(text("SELECT count(*) FROM exposure_bmn_residential WHERE id LIKE 'RESIDENTIAL%'")).scalar()
        res_bali_count = db.session.execute(text("SELECT count(*) FROM exposure_bmn_residential WHERE id LIKE 'RESIDENTIAL%' AND TRIM(LOWER(provinsi)) = 'bali'")).scalar()
        
        print(f"Total RESIDENTIAL: {res_count}")
        print(f"RESIDENTIAL in Bali: {res_bali_count}")
        
        if res_count > 0 and res_bali_count == 0:
             print("\nDIAGNOSIS: Database has Residential data but none are assigned to 'Bali' province.")
             distinct_provs = db.session.execute(text("SELECT DISTINCT provinsi FROM exposure_bmn_residential WHERE id LIKE 'RESIDENTIAL%'")).fetchall()
             print(f"Actual provinces for Residential: {[p[0] for p in distinct_provs]}")

if __name__ == "__main__":
    check_db()
