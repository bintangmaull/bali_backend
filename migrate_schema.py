import sys
import os

# Add backend dir to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.extensions import db
from sqlalchemy import text
from main import app
# app_instance = app.main.app # Old way
app_instance = app
with app_instance.app_context():
    print("Starting database schema migration...")
    try:
        with db.engine.connect() as conn:
            # 1. Increase VARCHAR limit for id_bangunan
            print("Enlarging id_bangunan column to VARCHAR(100)...")
            conn.execute(text("ALTER TABLE bangunan_copy ALTER COLUMN id_bangunan TYPE VARCHAR(100);"))
            conn.execute(text("ALTER TABLE hasil_proses_directloss ALTER COLUMN id_bangunan TYPE VARCHAR(100);"))
            print("Column enlargement successful.")

            # 2. Add missing AAL columns for 'res' category
            print("Adding missing AAL and exposure columns...")
            columns_to_add = [
                "aal_pga_res", "aal_inundansi_res", "aal_r_res", "aal_rc_res",
                "hotel", "res", "airport"
            ]
            for col in columns_to_add:
                try:
                    conn.execute(text(f"ALTER TABLE hasil_aal_kota ADD COLUMN IF NOT EXISTS {col} FLOAT8 DEFAULT 0;"))
                    print(f"Column {col} added or already exists.")
                except Exception as ex:
                    print(f"Warning adding column {col}: {ex}")

            # 2. Check and Drop Unique constraints on kota/provinsi in bangunan_copy
            print("Checking for unique constraints on bangunan_copy (kota/provinsi)...")
            # Query for unique constraints on buildings_copy
            constraints = conn.execute(text("""
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = 'bangunan_copy'::regclass
                AND contype = 'u';
            """)).fetchall()
            
            for r in constraints:
                cname = r[0]
                if 'kota' in cname or 'provinsi' in cname:
                    print(f"Dropping unique constraint: {cname}")
                    conn.execute(text(f"ALTER TABLE bangunan_copy DROP CONSTRAINT \"{cname}\";"))

            conn.commit()
            print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")
