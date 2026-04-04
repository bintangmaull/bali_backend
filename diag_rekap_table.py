import sys
import os
from sqlalchemy import text

# Add backend dir to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.extensions import db
from main import app

def check_rekap_table():
    with app.app_context():
        try:
            print("Checking columns in rekap_aset_kota...")
            res = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'rekap_aset_kota'
            """)).fetchall()
            cols = [r[0] for r in res]
            print(f"Columns: {cols}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_rekap_table()
