from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    rows = db.session.execute(text("SELECT exposure, climate_change, COUNT(*) FROM aal_flood_building GROUP BY exposure, climate_change")).fetchall()
    for row in rows:
        print(f"Exposure: {row[0]}, Climate: {row[1]}, Count: {row[2]}")

    print("\nSample AAL values:")
    rows = db.session.execute(text("SELECT exposure, climate_change, aal FROM aal_flood_building WHERE aal > 0 LIMIT 10")).fetchall()
    for row in rows:
        print(f"Exposure: {row[0]}, Climate: {row[1]}, AAL: {row[2]}")
