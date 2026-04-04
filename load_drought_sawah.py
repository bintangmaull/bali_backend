"""
Load drought sawah loss values from CSV into loss_drought_sawah table.
Run this once from the backend root:
    python load_drought_sawah.py
"""
import sys
import os
import csv

sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db
from sqlalchemy import text

CSV_PATH = r'E:\Dashboard\Data\Hasil\hasilsawah\Fixed Result - Rice Field\drought_loss_value.csv'

def parse_idr(val: str) -> float:
    """Parse IDR value that may contain commas as thousand separators."""
    try:
        return float(val.replace(',', '').strip())
    except (ValueError, AttributeError):
        return 0.0

def main():
    app = create_app()
    with app.app_context():
        # Create table if not already exists
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS loss_drought_sawah (
                id SERIAL PRIMARY KEY,
                kota VARCHAR(255) NOT NULL,
                return_period INTEGER NOT NULL,
                climate_change VARCHAR(10) NOT NULL,
                loss_2022_idr DOUBLE PRECISION,
                loss_2025_idr DOUBLE PRECISION,
                loss_2028_idr DOUBLE PRECISION,
                loss_2022_usd DOUBLE PRECISION,
                loss_2025_usd DOUBLE PRECISION,
                loss_2028_usd DOUBLE PRECISION,
                UNIQUE(kota, return_period, climate_change)
            );
        """))
        db.session.commit()
        print("Table ensured.")

        rows_inserted = 0
        with open(CSV_PATH, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                kota = row['kota'].strip()
                rp = int(row['return_period'].strip())
                cc = row['climate_change'].strip().lower()

                db.session.execute(text("""
                    INSERT INTO loss_drought_sawah
                        (kota, return_period, climate_change,
                         loss_2022_idr, loss_2025_idr, loss_2028_idr,
                         loss_2022_usd, loss_2025_usd, loss_2028_usd)
                    VALUES
                        (:kota, :rp, :cc,
                         :l22_idr, :l25_idr, :l28_idr,
                         :l22_usd, :l25_usd, :l28_usd)
                    ON CONFLICT (kota, return_period, climate_change)
                    DO UPDATE SET
                        loss_2022_idr = EXCLUDED.loss_2022_idr,
                        loss_2025_idr = EXCLUDED.loss_2025_idr,
                        loss_2028_idr = EXCLUDED.loss_2028_idr,
                        loss_2022_usd = EXCLUDED.loss_2022_usd,
                        loss_2025_usd = EXCLUDED.loss_2025_usd,
                        loss_2028_usd = EXCLUDED.loss_2028_usd
                """), {
                    'kota': kota, 'rp': rp, 'cc': cc,
                    'l22_idr': parse_idr(row['2022_loss_value_idr']),
                    'l25_idr': parse_idr(row['2025_loss_value_idr']),
                    'l28_idr': parse_idr(row['2028_loss_value_idr']),
                    'l22_usd': parse_idr(row['2022_loss_value_usd']),
                    'l25_usd': parse_idr(row['2025_loss_value_usd']),
                    'l28_usd': parse_idr(row['2028_loss_value_usd']),
                })
                rows_inserted += 1

        db.session.commit()
        print(f"Done! {rows_inserted} rows inserted/updated.")

if __name__ == '__main__':
    main()
