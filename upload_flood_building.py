import csv
import sys
import os

# Add the current directory to sys.path so 'app' can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.models_database import AALFloodBuilding

CSV_PATH = r"E:\Dashboard\Data\Hasil\aalbanjir\Flood AAL PML\flood4_building_merge.csv"

def upload_data():
    app = create_app()
    with app.app_context():
        # Create table if not exists
        db.create_all()

        print("Dropping and recreating aal_flood_building table for schema update...")
        AALFloodBuilding.__table__.drop(db.engine, checkfirst=True)
        db.create_all()
        print("Table recreated.")

        inserted = 0
        print(f"Reading from {CSV_PATH}...")
        
        try:
            with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                for row in reader:
                    # Clean the city name
                    kota = row.get('KK_ID', '').strip().upper()
                    if not kota:
                        continue
                        
                    record = AALFloodBuilding(
                        exposure=row.get('Eksposure', '').strip(),
                        climate_change=row.get('Climate Change', '').strip(),
                        id_kota=kota,
                        cv=float(row.get('CV') or 0.15),
                        aal=float(row.get('AAL') or 0),
                        var_95=float(row.get('VaR_95%') or 0),
                        tvar_95=float(row.get('TVaR_95%') or 0),
                        var_99=float(row.get('VaR_99%') or 0),
                        tvar_99=float(row.get('TVaR_99%') or 0),
                        pml_25=float(row.get('PML_25') or 0),
                        pml_50=float(row.get('PML_50') or 0),
                        pml_100=float(row.get('PML_100') or 0),
                        pml_250=float(row.get('PML_250') or 0)
                    )
                    db.session.add(record)
                    inserted += 1
                    
                    if inserted % 100 == 0:
                        db.session.commit()
                        print(f"Inserted {inserted} rows...")

            db.session.commit()
            print(f"✅ Successfully inserted {inserted} rows into aal_flood_building.")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during upload: {e}")

if __name__ == "__main__":
    upload_data()
