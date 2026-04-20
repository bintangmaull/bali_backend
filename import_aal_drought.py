import sys
import os
import csv
from sqlalchemy import text

sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db

CSV_PATH = r'E:\Dashboard\Data\Hasil\aalkekeringan\drought_rice_field_combined.csv'

def parse_float(val: str) -> float:
    try:
        return float(val.replace(',', '').strip())
    except (ValueError, AttributeError):
        return 0.0

def main():
    app = create_app()
    with app.app_context():
        # Create table if not already exists (mirroring model)
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS aal_drought_sawah (
                id SERIAL PRIMARY KEY,
                year INTEGER NOT NULL,
                climate_change VARCHAR(10) NOT NULL,
                id_kota VARCHAR(100) NOT NULL,
                province_name VARCHAR(100),
                cv DOUBLE PRECISION,
                aal DOUBLE PRECISION,
                var_95 DOUBLE PRECISION,
                tvar_95 DOUBLE PRECISION,
                var_99 DOUBLE PRECISION,
                tvar_99 DOUBLE PRECISION,
                pml_25 DOUBLE PRECISION,
                pml_50 DOUBLE PRECISION,
                pml_100 DOUBLE PRECISION,
                pml_250 DOUBLE PRECISION,
                UNIQUE(year, climate_change, id_kota)
            );
        """))
        db.session.commit()
        print("Table 'aal_drought_sawah' ensured.")

        rows_inserted = 0
        with open(CSV_PATH, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Column names from CSV: Year,Climate_Change,KK_ID,Province_Name,CV,AAL,VaR_95%,TVaR_95%,VaR_99%,TVaR_99%,PML_25,PML_50,PML_100,PML_250
                data = {
                    'year': int(row['Year']),
                    'cc': row['Climate_Change'].strip().lower(),
                    'kota': row['KK_ID'].strip(),
                    'prov': row['Province_Name'].strip(),
                    'cv': parse_float(row['CV']),
                    'aal': parse_float(row['AAL']),
                    'var_95': parse_float(row['VaR_95%']),
                    'tvar_95': parse_float(row['TVaR_95%']),
                    'var_99': parse_float(row['VaR_99%']),
                    'tvar_99': parse_float(row['TVaR_99%']),
                    'pml_25': parse_float(row['PML_25']),
                    'pml_50': parse_float(row['PML_50']),
                    'pml_100': parse_float(row['PML_100']),
                    'pml_250': parse_float(row['PML_250'])
                }

                db.session.execute(text("""
                    INSERT INTO aal_drought_sawah 
                        (year, climate_change, id_kota, province_name, cv, aal, var_95, tvar_95, var_99, tvar_99, pml_25, pml_50, pml_100, pml_250)
                    VALUES 
                        (:year, :cc, :kota, :prov, :cv, :aal, :var_95, :tvar_95, :var_99, :tvar_99, :pml_25, :pml_50, :pml_100, :pml_250)
                    ON CONFLICT (year, climate_change, id_kota) 
                    DO UPDATE SET
                        aal = EXCLUDED.aal,
                        cv = EXCLUDED.cv,
                        var_95 = EXCLUDED.var_95,
                        tvar_95 = EXCLUDED.tvar_95,
                        var_99 = EXCLUDED.var_99,
                        tvar_99 = EXCLUDED.tvar_99,
                        pml_25 = EXCLUDED.pml_25,
                        pml_50 = EXCLUDED.pml_50,
                        pml_100 = EXCLUDED.pml_100,
                        pml_250 = EXCLUDED.pml_250
                """), data)
                rows_inserted += 1

        db.session.commit()
        print(f"Success! Imported {rows_inserted} rows into 'aal_drought_sawah'.")

if __name__ == '__main__':
    main()
