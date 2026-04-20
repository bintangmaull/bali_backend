from sqlalchemy import text
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    # Update Skema 1
    db.session.execute(text("UPDATE aal_flood_sawah SET kota = 'KOTA DENPASAR' WHERE kota = 'DENPASAR'"))
    
    # Check if Skema 2 has KLUNGKUI
    r = db.session.execute(text("SELECT id FROM aal_flood_sawah_skema2 WHERE kota = 'KLUNGKUI'")).fetchall()
    if r:
        print(f"Found {len(r)} rows with 'KLUNGKUI' in Skema 2. Correcting to 'KLUNGKUNG'...")
        db.session.execute(text("UPDATE aal_flood_sawah_skema2 SET kota = 'KLUNGKUNG' WHERE kota = 'KLUNGKUI'"))
    
    db.session.commit()
    print("Database update completed.")
