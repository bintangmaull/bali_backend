import pandas as pd
from app import create_app, db
from app.models.models_database import AALFloodSawah

def upload():
    app = create_app()
    with app.app_context():
        # Clear existing data to avoid duplicates/confusion
        db.session.query(AALFloodSawah).delete()
        
        file_path = r"E:\Dashboard\Data\Hasil\aalbanjir\Flood AAL PML\flood4_rice_field_merge.csv"
        df = pd.read_csv(file_path, sep=';')
        
        for _, row in df.iterrows():
            # Map Rainfall -> ncc, Rainfall-Change -> cc
            raw_cc = str(row['Climate Change']).strip()
            cc_val = 'ncc' if raw_cc == 'Rainfall' else 'cc'
            
            entry = AALFloodSawah(
                year=int(row['Tahun']),
                climate_change=cc_val,
                kota=str(row['KK_ID']).replace('KOTA ', '').upper(),
                aal=float(row['AAL']) * 1_000_000_000, # Assuming B to absolute
                pml_10=float(row['PML10']) * 1_000_000_000,
                tvar_10=float(row['TVaR10']) * 1_000_000_000,
                pml_25=float(row['PML25']) * 1_000_000_000,
                tvar_25=float(row['TVaR25']) * 1_000_000_000,
                pml_50=float(row['PML50']) * 1_000_000_000,
                tvar_50=float(row['TVaR50']) * 1_000_000_000,
                pml_100=float(row['PML100']) * 1_000_000_000,
                tvar_100=float(row['TVaR100']) * 1_000_000_000,
                pml_250=float(row['PML250']) * 1_000_000_000,
                tvar_250=float(row['TVaR250']) * 1_000_000_000
            )
            db.session.add(entry)
        
        db.session.commit()
        print(f"Successfully uploaded {len(df)} rows to aal_flood_sawah table.")

if __name__ == "__main__":
    upload()
