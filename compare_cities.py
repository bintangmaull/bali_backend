from sqlalchemy import text
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    r1 = db.session.execute(text("SELECT DISTINCT kota FROM aal_flood_sawah")).fetchall()
    print("Skema 1 Cities:")
    for row in r1:
        print(f"- '{row[0]}'")
    
    r2 = db.session.execute(text("SELECT DISTINCT kota FROM aal_flood_sawah_skema2")).fetchall()
    print("\nSkema 2 Cities:")
    for row in r2:
        print(f"- '{row[0]}'")
