import sys
import os
import csv
from sqlalchemy import text

# Add backend dir to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.extensions import db
from app.models.models_database import HasilPMLGempaKota
from main import app

CSV_PATH = r"E:\Dashboard\Data\Hasil\aal gempa\AAL PML\pml_all.csv"

def migrate_pml():
    with app.app_context():
        print("Starting PML migration...")
        
        # 1. Create table if not exists
        try:
            db.create_all()
            print("Table created or already exists.")
        except Exception as e:
            print(f"Error creating table: {e}")
            return

        # 2. Import CSV data
        print(f"Reading CSV from {CSV_PATH}...")
        try:
            with open(CSV_PATH, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                # Clear existing data first to avoid primary key conflicts on re-run
                db.session.query(HasilPMLGempaKota).delete()
                
                for row in reader:
                    kota = row['kota'].strip().upper()
                    rp = int(row['return_period'])
                    
                    def clean_float(val):
                        if not val or val.strip() == '':
                            return 0.0
                        return float(val.replace(',', '.'))

                    pml_data = HasilPMLGempaKota(
                        id_kota=kota,
                        return_period=rp,
                        pml_airport=clean_float(row['pml_airport']),
                        pml_fd=clean_float(row['pml_fd']),
                        pml_electricity=clean_float(row['pml_electricity']),
                        pml_fs=clean_float(row['pml_fs']),
                        pml_hotel=clean_float(row['pml_hotel']),
                        pml_bmn=clean_float(row['pml_bmn']),
                        pml_res=clean_float(row['pml_res'])
                    )
                    db.session.add(pml_data)
                
                db.session.commit()
                print("PML data imported successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error importing CSV: {e}")

if __name__ == "__main__":
    migrate_pml()
