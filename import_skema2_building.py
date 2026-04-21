import pandas as pd
from app import create_app
from app.extensions import db
from app.models.models_database import AALFloodBuildingSkema2

file_path = r"E:\Dashboard\Data\Hasil\aalbanjir\Flood AAL PML\flood7_building_merge.csv"

def import_data():
    app = create_app()
    with app.app_context():
        # Buat tabel jika belum ada
        db.create_all()
        
        print(f"Reading CSV from: {file_path}")
        df = pd.read_csv(file_path, sep=';')
        
        # Hapus data lama agar tidak duplicate
        db.session.query(AALFloodBuildingSkema2).delete()
        
        records = []
        def clean_val(v):
            if pd.isna(v): return 0
            # Strip dots as they might be misinterpreted thousands separators or scaling dots
            return float(str(v).replace('.', '').replace(',', '.'))

        for index, row in df.iterrows():
            exposure = str(row['Eksposure']).strip()
            cc = str(row['Climate_Change']).strip()
            kota = str(row['KK_ID']).strip()
            
            record = AALFloodBuildingSkema2(
                exposure=exposure,
                climate_change=cc,
                kota=kota,
                aal=clean_val(row['AAL']),
                pml_2=clean_val(row['PML 2y']),
                pml_5=clean_val(row['PML 5y']),
                pml_10=clean_val(row['PML 10y']),
                pml_25=clean_val(row['PML 25y']),
                pml_50=clean_val(row['PML 50y']),
                pml_100=clean_val(row['PML 100y']),
                pml_250=clean_val(row['PML 250y'])
            )
            records.append(record)
            
        db.session.add_all(records)
        db.session.commit()
        print(f"Successfully inserted {len(records)} records into aal_flood_building_skema2.")

if __name__ == '__main__':
    import_data()
