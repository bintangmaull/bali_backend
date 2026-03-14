
import os
import sys
from sqlalchemy import text
from app.extensions import db
from app.config import Config
from flask import Flask

def check_dmgratio_schemas():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        tables = [
            'dmg_ratio_gempa', 
            'dmg_ratio_tsunami', 
            'dmg_ratio_banjir_r', 
            'dmg_ratio_banjir_rc',
            'model_intensitas_gempa',
            'model_intensitas_tsunami',
            'model_intensitas_banjir_r',
            'model_intensitas_banjir_rc'
        ]
        
        print("Schema verification for id_lokasi:")
        for tname in tables:
            q = text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{tname}' AND column_name = 'id_lokasi'
            """)
            col = db.session.execute(q).fetchone()
            if col:
                print(f"Table: {tname:30} | Column: {col.column_name:10} | Type: {col.data_type}")
            else:
                print(f"Table: {tname:30} | Column 'id_lokasi' NOT FOUND")

if __name__ == "__main__":
    check_dmgratio_schemas()
