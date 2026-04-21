import csv
import os
from app import create_app
from app.extensions import db
from app.models.models_database import TsunamiRiskResults

app = create_app()

CSV_PATH = r"E:\Dashboard\Data\Hasil\aaltsunami\tsunami_merge.csv"

def clean_float(val):
    if not val:
        return 0.0
    try:
        # Remove commas and handle percentage if any
        return float(val.replace(',', ''))
    except ValueError:
        return 0.0

def import_data():
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at {CSV_PATH}")
        return

    with app.app_context():
        print("Clearing existing tsunami_risk_results...")
        try:
            db.session.query(TsunamiRiskResults).delete()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing table: {e}")
            return
        
        print(f"Reading CSV from {CSV_PATH}...")
        try:
            with open(CSV_PATH, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                count = 0
                for row in reader:
                    loc_sector = row.get('KK_ID', '')
                    if not loc_sector or '_' not in loc_sector:
                        continue
                    
                    # Handle cases like "Denpasar City_Educational"
                    parts = loc_sector.rsplit('_', 1)
                    if len(parts) < 2:
                        continue
                        
                    kota = parts[0]
                    exposure = parts[1]

                    res = TsunamiRiskResults(
                        kota=kota,
                        exposure=exposure,
                        aal=0.0,  # Default to 0 as requested
                        actual_cv=clean_float(row.get('Actual_CV', 0)),
                        var_90=clean_float(row.get('VaR_90%', 0)),
                        tvar_90=clean_float(row.get('TVaR_90%', 0)),
                        var_95=clean_float(row.get('VaR_95%', 0)),
                        tvar_95=clean_float(row.get('TVaR_95%', 0)),
                        var_98=clean_float(row.get('VaR_98%', 0)),
                        tvar_98=clean_float(row.get('TVaR_98%', 0)),
                        var_99=clean_float(row.get('VaR_99%', 0)),
                        tvar_99=clean_float(row.get('TVaR_99%', 0)),
                        var_995=clean_float(row.get('VaR_99.5%', 0)),
                        tvar_995=clean_float(row.get('TVaR_99.5%', 0))
                    )
                    db.session.add(res)
                    count += 1
                
                db.session.commit()
                print(f"Successfully imported {count} rows into tsunami_risk_results.")
        except Exception as e:
            db.session.rollback()
            print(f"Error importing data: {e}")

if __name__ == "__main__":
    import_data()
