from sqlalchemy import text
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    result = db.session.execute(text("SELECT DISTINCT kota FROM aal_flood_sawah")).fetchall()
    print("Cities in aal_flood_sawah:")
    for row in result:
        print(f"- {row[0]}")
    
    result = db.session.execute(text("SELECT * FROM aal_flood_sawah WHERE kota ILIKE '%DENPASAR%'")).fetchall()
    print(f"\nFound {len(result)} rows for DENPASAR in aal_flood_sawah.")
    if result:
        for row in result[:5]:
            print(row)
