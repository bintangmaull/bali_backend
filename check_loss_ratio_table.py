import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db

app = create_app()

def check_table():
    with app.app_context():
        print("Checking LossRatioGempa table contents...")
        rows = db.session.execute(text("SELECT * FROM loss_ratio_gempa LIMIT 5")).fetchall()
        for r in rows:
            print(f"Row: {r}")

if __name__ == "__main__":
    check_table()
