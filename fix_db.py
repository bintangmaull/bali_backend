import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db

app = create_app()

def fix_db():
    with app.app_context():
        print("Fixing swapped columns for Residential data...")
        
        # SQL to swap kota and provinsi where kota is BALI and ID starts with RESIDENTIAL
        sql_fix = text("""
            UPDATE exposure_bmn_residential 
            SET kota = provinsi, 
                provinsi = 'BALI' 
            WHERE id LIKE 'RESIDENTIAL%' 
              AND TRIM(UPPER(kota)) = 'BALI';
        """)
        
        result = db.session.execute(sql_fix)
        db.session.commit()
        print(f"Update successful. Rows affected: {result.rowcount}")
        
        # Verify again
        res_bali_count = db.session.execute(text("SELECT count(*) FROM exposure_bmn_residential WHERE id LIKE 'RESIDENTIAL%' AND TRIM(LOWER(provinsi)) = 'bali'")).scalar()
        print(f"RESIDENTIAL now in Bali: {res_bali_count}")

if __name__ == "__main__":
    fix_db()
