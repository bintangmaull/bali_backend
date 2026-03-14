
import os
import sys
import pandas as pd
from sqlalchemy import text
from app.extensions import db
from app.config import Config
from flask import Flask

def check_db():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Checking tables and indices...")
        tables = [
            'bangunan_copy', 
            'model_intensitas_gempa', 
            'model_intensitas_tsunami', 
            'model_intensitas_banjir_r', 
            'model_intensitas_banjir_rc'
        ]
        
        q_idx = text("""
            SELECT tablename, indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename IN :tables
        """)
        indices = db.session.execute(q_idx, {"tables": tuple(tables)}).fetchall()
        
        print("\n--- INDICES ---")
        for idx in indices:
            print(f"{idx.tablename:30} | {idx.indexname:30} | {idx.indexdef}")
            
        q_rows = text("""
            SELECT relname as tablename, n_live_tup as row_count 
            FROM pg_stat_user_tables 
            WHERE relname IN :tables
        """)
        rows = db.session.execute(q_rows, {"tables": tuple(tables)}).fetchall()
        
        print("\n--- ROW COUNTS ---")
        for r in rows:
            print(f"{r.tablename:30} | {r.row_count}")

if __name__ == "__main__":
    check_db()
