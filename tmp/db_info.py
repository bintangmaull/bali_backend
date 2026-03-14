
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

def get_info():
    queries = {
        "table_sizes": """
            SELECT
                relname AS "Table",
                pg_size_pretty(pg_total_relation_size(c.oid)) AS "Total_Size",
                pg_size_pretty(pg_relation_size(c.oid)) AS "Table_Size",
                pg_size_pretty(pg_total_relation_size(c.oid) - pg_relation_size(c.oid)) AS "Index_Size",
                reltuples::bigint AS "Approx_Rows"
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public'
            AND c.relkind = 'r'
            AND c.relname IN ('model_intensitas_banjir', 'dmg_ratio_banjir', 'model_intensitas_banjir_r', 'model_intensitas_banjir_rc')
            ORDER BY pg_total_relation_size(c.oid) DESC;
        """,
        "column_types": """
            SELECT table_name, column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'model_intensitas_banjir'
            ORDER BY ordinal_position;
        """
    }
    
    with engine.connect() as conn:
        for name, query in queries.items():
            print(f"\n--- {name.upper()} ---")
            df = pd.read_sql(text(query), conn)
            print(df.to_string())

if __name__ == "__main__":
    get_info()
