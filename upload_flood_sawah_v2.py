import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Add app directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from app.config import Config
from app.models.models_database import AALFloodSawah

# Database connection using App Config
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

CSV_PATH = r"E:\Dashboard\Data\Hasil\aalbanjir\Flood AAL PML\flood4_rice_field_merge.csv"

def upload_data():
    try:
        # Load CSV
        df = pd.read_csv(CSV_PATH, sep=';')
        print(f"Loaded {len(df)} rows from CSV.")
        
        # Clear existing data
        session.query(AALFloodSawah).delete()
        print("Cleared existing flood sawah aal data.")
        
        for _, row in df.iterrows():
            scenario = 'cc' if row['Climate Change'] == 'CC' else 'ncc'
            
            aal_obj = AALFloodSawah(
                year=int(row['Tahun']),
                climate_change=scenario,
                kota=row['KK_ID'],
                aal=float(row['AAL']) * 1e9,
                pml_10=float(row['PML10']) * 1e9,
                tvar_10=float(row['TVaR10']) * 1e9,
                pml_25=float(row['PML25']) * 1e9,
                tvar_25=float(row['TVaR25']) * 1e9,
                pml_50=float(row['PML50']) * 1e9,
                tvar_50=float(row['TVaR50']) * 1e9,
                pml_100=float(row['PML100']) * 1e9,
                tvar_100=float(row['TVaR100']) * 1e9,
                pml_250=float(row['PML250']) * 1e9,
                tvar_250=float(row['TVaR250']) * 1e9
            )
            session.add(aal_obj)
            
        session.commit()
        print(f"Successfully uploaded {len(df)} rows with TVaR data.")
        
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    upload_data()
