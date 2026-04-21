from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    sql = text("SELECT DISTINCT climate_change FROM aal_flood_building")
    results = db.session.execute(sql).fetchall()
    print("Climate Change labels:", [r[0] for r in results])
    
    sql = text("SELECT DISTINCT id_kota FROM aal_flood_building LIMIT 10")
    results = db.session.execute(sql).fetchall()
    print("City samples:", [r[0] for r in results])
    
    sql = text("SELECT DISTINCT cv FROM aal_flood_building")
    results = db.session.execute(sql).fetchall()
    print("CV labels:", [r[0] for r in results])
