import sys
import os
import pandas as pd
from sqlalchemy import text

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db
from app.models.models_database import LossRatioGempa

app = create_app()

def populate_loss_ratio():
    csv_path = r"E:\Dashboard\Data\Hasil\hasilgempa\loss_ratio_gempa.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return

    # Read CSV with semicolon delimiter
    df = pd.read_csv(csv_path, sep=';')
    
    # Clean column names (lowercase and underscore)
    df.columns = [c.strip().lower().replace(' ', '_') for c in df.columns]
    
    # Rename 'hotel_loss_ratio' if it was 'hotel_loss_ratio' (it was 'hotel_Loss Ratio')
    # Actually my cleaning should handle 'hotel_loss_ratio'
    print(f"Columns found: {df.columns.tolist()}")

    with app.app_context():
        # Create table if not exists
        db.create_all()
        
        # Clear existing data
        db.session.query(LossRatioGempa).delete()
        
        # Insert data
        for _, row in df.iterrows():
            # Handle possible empty values (NaN)
            def clean_val(val):
                if pd.isna(val) or val == '':
                    return 0.0
                return float(val)

            lr = LossRatioGempa(
                kota=row['kota'],
                return_period=int(row['return_period']),
                airport_loss_ratio=clean_val(row.get('airport_loss_ratio', 0)),
                educational_loss_ratio=clean_val(row.get('educational_loss_ratio', 0)),
                electricity_loss_ratio=clean_val(row.get('electricity_loss_ratio', 0)),
                healthcare_loss_ratio=clean_val(row.get('healthcare_loss_ratio', 0)),
                hotel_loss_ratio=clean_val(row.get('hotel_loss_ratio', 0)),
                residential_loss_ratio=clean_val(row.get('residential_loss_ratio', 0)),
                bmn_loss_ratio=clean_val(row.get('bmn_loss_ratio', 0))
            )
            db.session.add(lr)
        
        db.session.commit()
        print(f"Successfully populated {len(df)} rows into loss_ratio_gempa table.")

if __name__ == "__main__":
    populate_loss_ratio()
