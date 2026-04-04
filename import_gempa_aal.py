import sys
import os
import csv

# Add backend dir to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.extensions import db
from app.models.models_database import HasilAALProvinsi
from sqlalchemy import text
from main import app

CSV_PATH = r"E:\Dashboard\Data\Hasil\aal gempa\AAL PML\aal.csv"

# Mapping from CSV 'exposure' column value to DB column suffix
# CSV value -> DB column suffix (aal_pga_...)
MAPPING = {
    'airport': 'airport',
    'res': 'res',
    'electricity': 'electricity',
    'bmn': 'bmn',
    'fd': 'fd',
    'fs': 'fs',
    'hotel': 'hotel'
}

def import_gempa_aal():
    print(f"Starting import from {CSV_PATH}...")
    
    # Read CSV
    data_per_kota = {} # kota -> {suffix: value}
    
    try:
        with open(CSV_PATH, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                kota = row['kota'].strip().upper()
                exposure_type = row['exposure'].strip().lower()
                aal_value_str = row['aal'].strip()
                
                if not aal_value_str:
                    aal_value = 0.0
                else:
                    try:
                        aal_value = float(aal_value_str)
                    except ValueError:
                        aal_value = 0.0
                
                if kota not in data_per_kota:
                    data_per_kota[kota] = {}
                
                if exposure_type in MAPPING:
                    suffix = MAPPING[exposure_type]
                    data_per_kota[kota][suffix] = aal_value
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    # Update Database
    with app.app_context():
        try:
            # 1. Clear ALL existing Gempa (PGA) data first
            print("Zeroing out existing Gempa (PGA) columns...")
            gempa_cols = [f"aal_pga_{s}" for s in MAPPING.values()] + ["aal_pga_total"]
            
            # Use raw SQL for efficiency to zero out all rows
            set_clause = ", ".join([f"{col} = 0" for col in gempa_cols if hasattr(HasilAALProvinsi, col)])
            if set_clause:
                db.session.execute(text(f"UPDATE hasil_aal_kota SET {set_clause}"))
                print("Existing Gempa data zeroed out.")

            # 2. Import new data
            for kota, values in data_per_kota.items():
                record = HasilAALProvinsi.query.filter(HasilAALProvinsi.id_kota.ilike(kota)).first()
                
                if not record:
                    print(f"City {kota} not found in database. Skipping...")
                    continue
                
                total_aal_kota = 0.0
                for suffix, val in values.items():
                    col_name = f"aal_pga_{suffix}"
                    if hasattr(record, col_name):
                        setattr(record, col_name, val)
                        total_aal_kota += val
                    else:
                        print(f"Warning: Model does not have column {col_name}")
                
                # Update total for this city
                record.aal_pga_total = total_aal_kota
                print(f"Updated {kota}: total_aal_pga = {total_aal_kota}")
            
            db.session.commit()
            print("Individual city data imported.")

            # 3. Calculate and update "Total Keseluruhan"
            print("Updating 'Total Keseluruhan' row...")
            total_rec = HasilAALProvinsi.query.filter(HasilAALProvinsi.id_kota == "Total Keseluruhan").first()
            if not total_rec:
                total_rec = HasilAALProvinsi(id_kota="Total Keseluruhan")
                db.session.add(total_rec)
            
            # Get all columns except id_kota
            all_cols = [c.key for c in HasilAALProvinsi.__table__.columns if c.key != 'id_kota']
            
            # Sum up all rows where id_kota != 'Total Keseluruhan'
            sum_results = db.session.query(
                *[db.func.sum(getattr(HasilAALProvinsi, c)).label(c) for c in all_cols]
            ).filter(HasilAALProvinsi.id_kota != "Total Keseluruhan").first()
            
            if sum_results:
                for col in all_cols:
                    val = getattr(sum_results, col) or 0.0
                    setattr(total_rec, col, val)
                print("Total Keseluruhan updated.")
            
            db.session.commit()
            print("Import and Totaling completed successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating database: {e}")

if __name__ == "__main__":
    import_gempa_aal()
