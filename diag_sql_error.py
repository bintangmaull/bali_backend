import os
import sys
from sqlalchemy import text
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Mocking app to get db session
app = Flask(__name__)
# Assuming standard local config
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/capstone_aal'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

with app.app_context():
    try:
        sql = """
        SELECT 
            p.id_provinsi as id_prov, r.id_kota, r.nama_kota,
            r.count_total, r.total_asset_total,
            ST_AsGeoJSON(ST_SimplifyPreserveTopology(r.geom, 0.005))::json as geom_geojson,
            r.dl_exposure
        FROM rekap_aset_kota r
        LEFT JOIN provinsi p ON TRIM(LOWER(r.provinsi)) = TRIM(LOWER(p.provinsi))
        """
        print("Executing query...")
        result = db.session.execute(text(sql)).fetchall()
        print(f"Success! Found {len(result)} rows.")
    except Exception as e:
        print(f"Error: {e}")
