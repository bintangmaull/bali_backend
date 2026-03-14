
import os
import sys
import io
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus
import traceback

# Force UTF-8 for everything
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

DB_USER = 'postgres.btwsqklqtqgrlmvysgsc'
DB_PASSWORD = '@Guyengan123'
DB_HOST = 'aws-1-ap-northeast-1.pooler.supabase.com'
DB_PORT = '5432'
DB_NAME = 'postgres'
safe_password = quote_plus(DB_PASSWORD)
SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{safe_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require'

engine = create_engine(SQLALCHEMY_DATABASE_URI)

def run_optimization():
    # Read with UTF-8
    with open("database_optimization.sql", "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split commands by semicolon
    commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
    
    log_file = "tmp/optimization_log.txt"
    with open(log_file, "w", encoding="utf-8") as log:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            for i, cmd in enumerate(commands):
                # Clean up command for logging
                clean_cmd = "\n".join([line for line in cmd.splitlines() if not line.strip().startswith('--')])
                if not clean_cmd.strip():
                    continue
                
                log.write(f"\n--- EXECUTING COMMAND {i+1} ---\n{clean_cmd}\n")
                print(f"Executing command {i+1}/{len(commands)}...")
                try:
                    conn.execute(text(clean_cmd))
                    log.write("✅ SUCCESS\n")
                    print(f"✅ Success (Cmd {i+1})")
                except Exception as e:
                    log.write(f"❌ FAILED: {str(e)}\n")
                    log.write(traceback.format_exc())
                    print(f"❌ Failed (Cmd {i+1})")

if __name__ == "__main__":
    run_optimization()
