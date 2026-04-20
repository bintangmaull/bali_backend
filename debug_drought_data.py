import pandas as pd
from app import create_app
from app.extensions import db
from sqlalchemy import text
import json

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        print("--- Checking aal_drought_sawah data distribution ---")
        q_stats = """
        SELECT year, climate_change, COUNT(*), SUM(aal) as total_aal
        FROM aal_drought_sawah
        GROUP BY year, climate_change
        ORDER BY year, climate_change;
        """
        stats = pd.read_sql(text(q_stats), conn)
        print(stats)
        
        print("\n--- Checking sample data for Badung 2025 CC ---")
        q_sample = """
        SELECT id_kota, year, climate_change, aal
        FROM aal_drought_sawah
        WHERE id_kota ILIKE '%Badung%' AND year = 2025 AND climate_change = 'cc'
        LIMIT 5;
        """
        sample = pd.read_sql(text(q_sample), conn)
        print(sample)
