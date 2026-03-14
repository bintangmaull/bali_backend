
from app.extensions import db
from app.config import Config
from flask import Flask
from sqlalchemy import text

def check():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        # Seberapa jauh titik tsunami terdekat dari bangunan?
        print("Cek jarak minimum titik tsunami terdekat dari 10 bangunan pertama:")
        q = text("""
            SELECT b.id_bangunan,
                   MIN(ST_Distance(b.geom::geography, r.geom::geography)) AS jarak_min_meter
            FROM (SELECT id_bangunan, geom FROM bangunan_copy LIMIT 10) b
            CROSS JOIN model_intensitas_tsunami r
            GROUP BY b.id_bangunan
            ORDER BY jarak_min_meter
        """)
        rows = db.session.execute(q).fetchall()
        for row in rows:
            print(f"  id={row.id_bangunan}, jarak terdekat ke tsunami: {row.jarak_min_meter:.1f}m")
        
        print()
        print("Jumlah bangunan yg punya titik tsunami dalam radius 1km:")
        q2 = text("""
            SELECT COUNT(DISTINCT b.id_bangunan) as cnt
            FROM bangunan_copy b
            JOIN model_intensitas_tsunami r ON ST_DWithin(b.geom::geography, r.geom::geography, 1000)
        """)
        cnt2 = db.session.execute(q2).scalar()
        print(f"  {cnt2}")
        
        print()
        print("Jumlah bangunan yg punya titik tsunami dalam radius 100km:")
        q3 = text("""
            SELECT COUNT(DISTINCT b.id_bangunan) as cnt
            FROM bangunan_copy b
            JOIN model_intensitas_tsunami r ON ST_DWithin(b.geom::geography, r.geom::geography, 100000)
        """)
        cnt3 = db.session.execute(q3).scalar()
        print(f"  {cnt3}")

if __name__ == "__main__":
    check()
