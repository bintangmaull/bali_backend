from app import db, create_app
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Check what risultato_aal_kota has for BADUNG's airport
    sql_hak = "SELECT id_kota, aal_r_airport, aal_r_total FROM hasil_aal_kota WHERE LOWER(TRIM(id_kota)) = 'badung'"
    res = db.session.execute(text(sql_hak)).fetchall()
    print("hasil_aal_kota for BADUNG:")
    for row in res:
        print(f"  id_kota={row[0]}, aal_r_airport={row[1]}, aal_r_total={row[2]}")

    # Check what aal_flood_building sums to for BADUNG at cv=0.15
    sql_fb = """
    SELECT 
        TRIM(LOWER(id_kota)) as kota,
        SUM(CASE WHEN climate_change = 'Rainfall' AND exposure = 'Airport' THEN aal ELSE 0 END) as airport_r,
        SUM(CASE WHEN climate_change = 'Rainfall' THEN aal ELSE 0 END) as total_r
    FROM aal_flood_building
    WHERE cv = 0.15 AND LOWER(TRIM(id_kota)) = 'badung'
    GROUP BY TRIM(LOWER(id_kota))
    """
    res2 = db.session.execute(text(sql_fb)).fetchall()
    print("\naal_flood_building for BADUNG at cv=0.15:")
    for row in res2:
        print(f"  kota={row[0]}, airport_r={row[1]}, total_r={row[2]}")
