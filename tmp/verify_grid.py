
import os
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

DB_USER = 'postgres.btwsqklqtqgrlmvysgsc'
DB_PASSWORD = '@Guyengan123'
DB_HOST = 'aws-1-ap-northeast-1.pooler.supabase.com'
DB_PORT = '5432'
DB_NAME = 'postgres'
safe_password = quote_plus(DB_PASSWORD)
SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require'

engine = create_engine(SQLALCHEMY_DATABASE_URI)

def verify_grid():
    query = """
        SELECT 
            (SELECT count(*) FROM model_intensitas_banjir_r) as count_r,
            (SELECT count(*) FROM model_intensitas_banjir_rc) as count_rc,
            (
                SELECT count(*) 
                FROM model_intensitas_banjir_r r
                JOIN model_intensitas_banjir_rc rc ON r.id_lokasi = rc.id_lokasi
                WHERE r.lon = rc.lon AND r.lat = rc.lat
            ) as matching_rows;
    """
    
    with engine.connect() as conn:
        print("\n--- GRID VERIFICATION ---")
        df = pd.read_sql(text(query), conn)
        print(df.to_string())

if __name__ == "__main__":
    verify_grid()
