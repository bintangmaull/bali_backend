import os
import sys

# Add the project directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.repository.repo_directloss import get_db_connection
from sqlalchemy import text

def generate_geom():
    try:
        engine = get_db_connection()
        with engine.begin() as conn:
            # Generate geometry using ST_MakePoint
            sql = text("""
                UPDATE model_intensitas_banjir 
                SET geom = ST_SetSRID(ST_MakePoint(lon, lat), 4326)
                WHERE lon IS NOT NULL AND lat IS NOT NULL;
            """)
            result = conn.execute(sql)
            print(f"Successfully generated/updated geom for {result.rowcount} rows in model_intensitas_banjir.")
    except Exception as e:
        print(f"Error updating geom: {e}")

if __name__ == "__main__":
    generate_geom()
