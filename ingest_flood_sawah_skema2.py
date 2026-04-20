import csv
from app import create_app
from app.extensions import db
from app.models.models_database import AALFloodSawahSkema2

def ingest_flood_sawah_skema2():
    app = create_app()
    with app.app_context():
        # Clear existing data in Skema 2 table
        print("Clearing existing Skema 2 data...")
        AALFloodSawahSkema2.query.delete()
        
        csv_path = r'E:\Dashboard\Data\Hasil\aalbanjir\Flood AAL PML\flood7_rice_field_merge.csv'
        
        print(f"Reading CSV from {csv_path}...")
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            rows_to_insert = []
            for row in reader:
                # Map Climate values: Rainfall -> ncc, Rainfall-Change -> cc
                climate = row['Climate']
                if climate == 'Rainfall':
                    cc_val = 'ncc'
                elif climate == 'Rainfall-Change':
                    cc_val = 'cc'
                else:
                    cc_val = climate.lower() # Fallback
                
                rows_to_insert.append(AALFloodSawahSkema2(
                    year=int(row['Tahun']),
                    climate_change=cc_val,
                    kota=row['Region'],
                    aal=float((row['AAL'] or '0').replace('.', '')),
                    pml_2=float((row['PML2'] or '0').replace('.', '')),
                    pml_5=float((row['PML5'] or '0').replace('.', '')),
                    pml_10=float((row['PML10'] or '0').replace('.', '')),
                    pml_25=float((row['PML25'] or '0').replace('.', '')),
                    pml_50=float((row['PML50'] or '0').replace('.', '')),
                    pml_100=float((row['PML100'] or '0').replace('.', '')),
                    pml_250=float((row['PML250'] or '0').replace('.', ''))
                ))
            
            if rows_to_insert:
                db.session.bulk_save_objects(rows_to_insert)
                db.session.commit()
                print(f"Successfully ingested {len(rows_to_insert)} rows into aal_flood_sawah_skema2.")
            else:
                print("No data found in CSV.")

if __name__ == '__main__':
    ingest_flood_sawah_skema2()
