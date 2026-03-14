
import os
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

def run_optimization():
    with open("database_optimization.sql", "r") as f:
        sql_script = f.read()

    # Split commands by semicolon, but be careful with comments and empty lines
    commands = [cmd.strip() for cmd in sql_script.split(';') if cmd.strip() and not cmd.strip().startswith('--')]

    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for cmd in commands:
            print(f"Executing: {cmd[:100]}...")
            try:
                conn.execute(text(cmd))
                print("✅ Success")
            except Exception as e:
                print(f"❌ Failed: {e}")

if __name__ == "__main__":
    run_optimization()
