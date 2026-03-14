
import os
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import traceback

DB_USER = 'postgres.btwsqklqtqgrlmvysgsc'
DB_PASSWORD = '@Guyengan123'
DB_HOST = 'aws-1-ap-northeast-1.pooler.supabase.com'
DB_PORT = '5432'
DB_NAME = 'postgres'
safe_password = quote_plus(DB_PASSWORD)
SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require'

engine = create_engine(SQLALCHEMY_DATABASE_URI)

def run_migration():
    with open("merge_flood_tables.sql", "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split commands by semicolon
    commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
    
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for i, cmd in enumerate(commands):
            # Clean up command for logging
            clean_cmd = "\n".join([line for line in cmd.splitlines() if not line.strip().startswith('--')])
            if not clean_cmd.strip():
                continue
            
            print(f"Executing command {i+1}/{len(commands)}...")
            try:
                conn.execute(text(clean_cmd))
                print(f"✅ Success (Cmd {i+1})")
            except Exception as e:
                print(f"❌ Failed (Cmd {i+1}): {str(e)[:100]}")

if __name__ == "__main__":
    run_migration()
