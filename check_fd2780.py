
import os
import pandas as pd
from app.extensions import db
from app.config import Config
from flask import Flask
from sqlalchemy import text
from app.repository.repo_directloss import get_all_disaster_data

def check_fd2780():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Checking building FD_2780 specifically...")
        
        # 1. Manual SQL check for this building
        sql = text("""
            SELECT
              b.id_bangunan, b.taxonomy,
              near.nilai_y_cr_inundansi,
              near.nilai_y_mcf_inundansi
            FROM (SELECT id_bangunan, geom, taxonomy FROM bangunan_copy WHERE id_bangunan = 'FD_2780') b
            JOIN LATERAL (
              SELECT
                h.dmgratio_cr_inundansi   AS nilai_y_cr_inundansi,
                h.dmgratio_mcf_inundansi  AS nilai_y_mcf_inundansi,
                ST_Distance(b.geom::geography, r.geom::geography) as dist
              FROM model_intensitas_tsunami r
              JOIN dmg_ratio_tsunami h USING(id_lokasi)
              WHERE ST_DWithin(
                b.geom::geography,
                r.geom::geography,
                110
              )
              ORDER BY b.geom::geography <-> r.geom::geography
              LIMIT 1
            ) AS near ON TRUE;
        """)
        res = db.session.execute(sql).fetchone()
        if res:
            print(f"SQL Result: {dict(res._mapping)}")
        else:
            print("SQL Result: No match found for FD_2780 within 110m (This shouldn't happen if previous distance check was 33m)")

        # 2. Check get_all_disaster_data results
        print("\nChecking get_all_disaster_data() output for FD_2780...")
        all_data = get_all_disaster_data()
        tsunami_df = all_data.get('tsunami')
        if tsunami_df is not None:
            row = tsunami_df[tsunami_df['id_bangunan'] == 'FD_2780']
            print(f"CSV/DF Row for FD_2780 in tsunami_data:\n{row}")
        else:
            print("Tsunami data not found in all_data")

if __name__ == "__main__":
    check_fd2780()
