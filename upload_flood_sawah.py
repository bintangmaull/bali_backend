"""
One-time script: Upload flood4_rice_field_merge.csv into the aal_flood_sawah table.
Run with:  python upload_flood_sawah.py
"""
import csv, sys, os

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models.models_database import AALFloodSawah

CSV_PATH = r"E:\Dashboard\Data\Hasil\aalbanjir\Flood AAL PML\flood4_rice_field_merge.csv"

BILLION = 1e9   # CSV values are already in IDR billions → multiply to store as IDR

app = create_app()

with app.app_context():
    # Create table if not exists
    db.create_all()

    # Clear existing data (idempotent re-run)
    deleted = AALFloodSawah.query.delete()
    db.session.commit()
    print(f"Cleared {deleted} existing rows.")

    inserted = 0
    with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            if not row.get('KK_ID'):
                continue

            cc_raw = row['Climate Change'].strip()
            cc = 'ncc' if cc_raw == 'Rainfall' else 'cc'

            record = AALFloodSawah(
                year=int(row['Tahun']),
                climate_change=cc,
                kota=row['KK_ID'].strip(),
                aal=float(row['AAL']) * BILLION,
                pml_10=float(row['PML10']) * BILLION,
                tvar_10=float(row['TVaR10']) * BILLION,
                pml_25=float(row['PML25']) * BILLION,
                tvar_25=float(row['TVaR25']) * BILLION,
                pml_50=float(row['PML50']) * BILLION,
                tvar_50=float(row['TVaR50']) * BILLION,
                pml_100=float(row['PML100']) * BILLION,
                tvar_100=float(row['TVaR100']) * BILLION,
                pml_250=float(row['PML250']) * BILLION,
                tvar_250=float(row['TVaR250']) * BILLION,
            )
            db.session.add(record)
            inserted += 1

    db.session.commit()
    print(f"✅ Successfully inserted {inserted} rows into aal_flood_sawah.")
