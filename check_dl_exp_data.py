import sys
import os
from sqlalchemy import text
import json

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db

app = create_app()

def check_data():
    with app.app_context():
        print("Checking rekap_aset_kota.dl_exposure for BADUNG...")
        row = db.session.execute(text("SELECT dl_exposure FROM rekap_aset_kota WHERE id_kota = 'BADUNG'")).fetchone()
        if row and row[0]:
            print("Data found:")
            data = row[0]
            if isinstance(data, str):
                data = json.loads(data)
            
            # Print a snippet of healthcare or airport data
            for cat in ['healthcare', 'airport', 'total']:
                if cat in data:
                    print(f"  Category {cat}: {data[cat]}")
        else:
            print("No data found for BADUNG.")

if __name__ == "__main__":
    check_data()
