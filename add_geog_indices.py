
import os
import sys
from sqlalchemy import text
from app.extensions import db
from app.config import Config
from flask import Flask

def add_indices():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        tables = [
            'model_intensitas_gempa',
            'model_intensitas_tsunami',
            'model_intensitas_banjir_r',
            'model_intensitas_banjir_rc'
        ]
        
        for table in tables:
            idx_name = f"idx_{table}_geog"
            print(f"Adding geography index to {table}...")
            try:
                # Cek apakah kolom geom ada (untuk gempa tadi mencurigakan)
                res = db.session.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='geom'")).fetchone()
                if not res:
                    print(f"⚠️ Table {table} has no 'geom' column. Skipping.")
                    continue
                
                db.session.execute(text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} USING gist ((geom::geography))"))
                db.session.commit()
                print(f"✅ Success: {idx_name}")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Failed for {table}: {e}")

if __name__ == "__main__":
    add_indices()
