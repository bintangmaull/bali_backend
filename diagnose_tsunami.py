
import os
import pandas as pd
import numpy as np
from app.extensions import db
from app.config import Config
from flask import Flask
from sqlalchemy import text

def diagnose():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("=" * 60)
        print("DIAGNOSA 1: Jumlah row di tabel terkait tsunami")
        r1 = db.session.execute(text("SELECT COUNT(*) FROM dmg_ratio_tsunami")).scalar()
        r2 = db.session.execute(text("SELECT COUNT(*) FROM model_intensitas_tsunami")).scalar()
        r3 = db.session.execute(text("SELECT COUNT(*) FROM referensi_dmgratio_tsunami")).scalar()
        print(f"  dmg_ratio_tsunami: {r1}")
        print(f"  model_intensitas_tsunami: {r2}")
        print(f"  referensi_dmgratio_tsunami: {r3}")
        
        print()
        print("DIAGNOSA 2: Contoh nilai dari dmg_ratio_tsunami")
        sample = db.session.execute(text("SELECT * FROM dmg_ratio_tsunami LIMIT 5")).fetchall()
        for row in sample:
            print(f"  {dict(row._mapping)}")
        
        print()
        print("DIAGNOSA 3: Contoh join lateral tsunami (threshold 110m)")
        q = text("""
            SELECT b.id_bangunan, 
                   n.dmgratio_cr_inundansi AS cr_val,
                   n.dmgratio_mcf_inundansi AS mcf_val
            FROM bangunan_copy b
            JOIN LATERAL (
                SELECT h.dmgratio_cr_inundansi, h.dmgratio_mcf_inundansi
                FROM model_intensitas_tsunami r
                JOIN dmg_ratio_tsunami h USING(id_lokasi)
                WHERE ST_DWithin(b.geom::geography, r.geom::geography, 110)
                ORDER BY b.geom::geography <-> r.geom::geography
                LIMIT 1
            ) n ON TRUE
            LIMIT 5
        """)
        rows = db.session.execute(q).fetchall()
        print(f"  Baris berhasil join (threshold 110m): {len(rows)}")
        for row in rows:
            print(f"  {dict(row._mapping)}")
        
        # Coba dengan threshold lebih besar
        print()
        print("DIAGNOSA 4: Test join lateral dengan threshold 10000m")
        q2 = text("""
            SELECT COUNT(*) as cnt
            FROM bangunan_copy b
            JOIN LATERAL (
                SELECT 1
                FROM model_intensitas_tsunami r
                WHERE ST_DWithin(b.geom::geography, r.geom::geography, 10000)
                LIMIT 1
            ) n ON TRUE
        """)
        cnt2 = db.session.execute(q2).scalar()
        print(f"  Bangunan yang match dalam 10km: {cnt2}")

    # DIAGNOSA 5: Periksa CSV
    csv_path = os.path.join("debug_output", "directloss_all.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, sep=';')
        print()
        print("=" * 60)
        print("DIAGNOSA 5: direct_loss_inundansi dari CSV")
        if 'direct_loss_inundansi' in df.columns:
            nonzero = df[df['direct_loss_inundansi'] > 0]
            print(f"  Baris NONZERO: {len(nonzero)} dari {len(df)}")
            print(df['direct_loss_inundansi'].describe())
        else:
            print(f"  KOLOM TIDAK ADA! Kolom: {list(df.columns)}")

if __name__ == "__main__":
    diagnose()
