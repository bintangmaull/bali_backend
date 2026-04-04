import sys
import os
from sqlalchemy import text

# Add backend dir to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.extensions import db
from main import app

def check_aal_table():
    with app.app_context():
        try:
            # 1. Check Columns
            print("Checking columns in hasil_aal_kota...")
            res = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'hasil_aal_kota'
            """)).fetchall()
            cols = [r[0] for r in res]
            print(f"Columns: {cols}")
            
            # 2. Check Data for first few rows
            print("\nChecking first row of data...")
            data = db.session.execute(text("SELECT * FROM hasil_aal_kota LIMIT 1")).mappings().first()
            if data:
                print(dict(data))
            else:
                print("Table is empty.")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_aal_table()
