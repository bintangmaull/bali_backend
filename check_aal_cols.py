
import os
import sys
from sqlalchemy import text
from app.extensions import db
from app.config import Config
from flask import Flask

def check_aal_tables():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Checking tables starting with 'hasil_aal_'...")
        q_tables = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_name LIKE 'hasil_aal_%'
        """)
        tables = db.session.execute(q_tables).fetchall()
        
        for t in tables:
            tname = t.table_name
            print(f"\n--- Table: {tname} ---")
            q_cols = text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{tname}'
                ORDER BY ordinal_position
            """)
            cols = db.session.execute(q_cols).fetchall()
            for col in cols:
                print(f"  {col.column_name:30} | {col.data_type}")

if __name__ == "__main__":
    check_aal_tables()
