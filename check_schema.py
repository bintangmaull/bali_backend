import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db

app = create_app()

def check_schema():
    with app.app_context():
        tables = ['rekap_aset_kota', 'provinsi']
        for table in tables:
            print(f"\nSchema for {table}:")
            try:
                sql = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table}'"
                cols = db.session.execute(text(sql)).fetchall()
                for col in cols:
                    print(f"  {col[0]}: {col[1]}")
            except Exception as e:
                print(f"Error checking {table}: {e}")

if __name__ == "__main__":
    check_schema()
