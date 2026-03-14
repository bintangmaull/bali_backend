import os
import sys

# Tambahkan path root proyek ke sys.path agar bisa import module app
sys.path.append('e:/Dashboard/backend-capstone-aal')

from sqlalchemy import text
from app import create_app
from app.extensions import db

app = create_app()

sql_script = """
-- 1. model_intensitas_banjir
ALTER TABLE model_intensitas_banjir
ADD COLUMN r_2 FLOAT,
ADD COLUMN r_5 FLOAT,
ADD COLUMN r_10 FLOAT,
ADD COLUMN rc_2 FLOAT,
ADD COLUMN rc_5 FLOAT,
ADD COLUMN rc_10 FLOAT;

-- 2. dmg_ratio_banjir
ALTER TABLE dmg_ratio_banjir
ADD COLUMN dmgratio_1_r2 FLOAT DEFAULT 0,
ADD COLUMN dmgratio_2_r2 FLOAT DEFAULT 0,
ADD COLUMN dmgratio_1_r5 FLOAT DEFAULT 0,
ADD COLUMN dmgratio_2_r5 FLOAT DEFAULT 0,
ADD COLUMN dmgratio_1_r10 FLOAT DEFAULT 0,
ADD COLUMN dmgratio_2_r10 FLOAT DEFAULT 0,
ADD COLUMN dmgratio_1_rc2 FLOAT DEFAULT 0,
ADD COLUMN dmgratio_2_rc2 FLOAT DEFAULT 0,
ADD COLUMN dmgratio_1_rc5 FLOAT DEFAULT 0,
ADD COLUMN dmgratio_2_rc5 FLOAT DEFAULT 0,
ADD COLUMN dmgratio_1_rc10 FLOAT DEFAULT 0,
ADD COLUMN dmgratio_2_rc10 FLOAT DEFAULT 0;

-- 3. hasil_proses_directloss
ALTER TABLE hasil_proses_directloss
ADD COLUMN direct_loss_r_2 FLOAT DEFAULT 0,
ADD COLUMN direct_loss_r_5 FLOAT DEFAULT 0,
ADD COLUMN direct_loss_r_10 FLOAT DEFAULT 0,
ADD COLUMN direct_loss_rc_2 FLOAT DEFAULT 0,
ADD COLUMN direct_loss_rc_5 FLOAT DEFAULT 0,
ADD COLUMN direct_loss_rc_10 FLOAT DEFAULT 0;

-- 4. rekap_aset_kota
ALTER TABLE rekap_aset_kota
ADD COLUMN dl_sum_r_2 FLOAT DEFAULT 0,
ADD COLUMN ratio_r_2 FLOAT DEFAULT 0,
ADD COLUMN dl_sum_r_5 FLOAT DEFAULT 0,
ADD COLUMN ratio_r_5 FLOAT DEFAULT 0,
ADD COLUMN dl_sum_r_10 FLOAT DEFAULT 0,
ADD COLUMN ratio_r_10 FLOAT DEFAULT 0,
ADD COLUMN dl_sum_rc_2 FLOAT DEFAULT 0,
ADD COLUMN ratio_rc_2 FLOAT DEFAULT 0,
ADD COLUMN dl_sum_rc_5 FLOAT DEFAULT 0,
ADD COLUMN ratio_rc_5 FLOAT DEFAULT 0,
ADD COLUMN dl_sum_rc_10 FLOAT DEFAULT 0,
ADD COLUMN ratio_rc_10 FLOAT DEFAULT 0;
"""

with app.app_context():
    statements = [s.strip() for s in sql_script.split(';') if s.strip()]
    for stmt in statements:
        try:
            db.session.execute(text(stmt))
            db.session.commit()
            print(f"Statement executed successfully: {stmt.splitlines()[0]}")
        except Exception as e:
            db.session.rollback()
            print(f"Error executing statement: {e}")
            if 'already exists' in str(e):
                print("Column might already exist, continuing...")
    print("Migration finished.")
