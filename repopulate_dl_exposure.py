# repopulate_dl_exposure.py - v3: uses psycopg2 directly for UPDATE
import sys, os
sys.path.insert(0, r'e:\Dashboard\backend-capstone-aal')

# Load config before Flask app to avoid issues
from app import create_app
app = create_app()

import psycopg2
import psycopg2.extras
from sqlalchemy import text
from app.extensions import db
import pandas as pd
import json

DISASTER_COLS = {
    # 'gempa' is handled separately via migrate_gempa_to_rekap.py for loss ratios
    'tsunami':  {'prefix': '',     'scales': ['inundansi']},
    'banjir_r': {'prefix': 'r',    'scales': ['2','5','10','25','50','100','250']},
    'banjir_rc':{'prefix': 'rc',   'scales': ['2','5','10','25','50','100','250']},
}

SUPPORTED_TYPES = ['fs', 'fd', 'electricity', 'hotel', 'airport']

def main():
    with app.app_context():
        # Get the raw DB connection string from the SQLAlchemy engine
        db_url = str(db.engine.url).replace('+psycopg2', '')
        print(f"Connecting via psycopg2...")
        
        # Load data via pandas
        print("Loading bangunan + direct loss...")
        sql = """
            SELECT b.kota, b.kode_bangunan, dl.*
            FROM bangunan_copy b
            JOIN hasil_proses_directloss dl ON b.id_bangunan = dl.id_bangunan
        """
        df = pd.read_sql(sql, db.engine)
        df['kode_bangunan'] = df['kode_bangunan'].fillna('').str.lower().str.strip()
        dl_cols = [c for c in df.columns if c.startswith('direct_loss_')]
        print(f"  Loaded {len(df)} rows, {len(dl_cols)} DL columns")

        # Compute dl_exposure per city
        print("Computing dl_exposure per city...")
        updates = []
        for kota, group in df.groupby('kota'):
            dl_exposure_dict = {}
            for name, cfg in DISASTER_COLS.items():
                pre = cfg['prefix']
                scales = cfg['scales']
                for s in scales:
                    rp_suffix = f"{pre}_{s}" if pre else s
                    dl_col = f"direct_loss_{rp_suffix}"
                    if dl_col not in df.columns:
                        continue
                    for btype in SUPPORTED_TYPES:
                        if btype not in dl_exposure_dict:
                            dl_exposure_dict[btype] = {}
                        sub = group[group['kode_bangunan'] == btype]
                        val = float(sub[dl_col].sum()) if len(sub) > 0 else 0.0
                        dl_exposure_dict[btype][rp_suffix] = val
            updates.append((kota, json.dumps(dl_exposure_dict)))

        print(f"  Built exposure data for {len(updates)} cities")

        # Update via psycopg2
        print("Updating dl_exposure in rekap_aset_kota...")
        raw_conn = db.engine.raw_connection()
        try:
            cur = raw_conn.cursor()
            # Add column if it doesn't exist
            cur.execute("""
                DO $$ BEGIN
                    IF NOT EXISTS (
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name='rekap_aset_kota' AND column_name='dl_exposure'
                    ) THEN
                        ALTER TABLE rekap_aset_kota ADD COLUMN dl_exposure jsonb;
                    END IF;
                END $$;
            """)
            raw_conn.commit()
            print("  Column ensured.")
            for kota, dlexp_json in updates:
                cur.execute(
                    "UPDATE rekap_aset_kota SET dl_exposure = %s::jsonb WHERE lower(id_kota) = lower(%s)",
                    (dlexp_json, kota)
                )
                print(f"  ✅ {kota}")
            raw_conn.commit()
            print("Done! dl_exposure updated successfully.")
        except Exception as e:
            raw_conn.rollback()
            raise e
        finally:
            raw_conn.close()

if __name__ == '__main__':
    main()
