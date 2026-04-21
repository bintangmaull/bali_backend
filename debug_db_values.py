from app import db, create_app
from sqlalchemy import text

app = create_app()
with app.app_context():
    sql = "SELECT DISTINCT climate_change, COUNT(*) FROM aal_flood_building GROUP BY climate_change"
    res = db.session.execute(text(sql)).fetchall()
    print("Unique climate_change values in aal_flood_building:")
    for row in res:
        print(f"Value: '{row[0]}', Count: {row[1]}")
    
    sql2 = "SELECT DISTINCT exposure, COUNT(*) FROM aal_flood_building GROUP BY exposure"
    res2 = db.session.execute(text(sql2)).fetchall()
    print("\nUnique exposure values in aal_flood_building:")
    for row in res2:
        print(f"Value: '{row[0]}', Count: {row[1]}")
