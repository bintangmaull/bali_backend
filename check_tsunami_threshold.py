
from app.extensions import db
from app.config import Config
from flask import Flask
from sqlalchemy import text

def check():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Jarak antar titik tsunami (estimasi grid spacing):")
        q = text("""
            SELECT AVG(dist) as avg_dist, MIN(dist) as min_dist, MAX(dist) as max_dist
            FROM (
                SELECT ST_Distance(
                    a.geom::geography,
                    b.geom::geography
                ) AS dist
                FROM (SELECT geom FROM model_intensitas_tsunami ORDER BY id_lokasi LIMIT 100) a
                CROSS JOIN LATERAL (
                    SELECT geom FROM model_intensitas_tsunami 
                    WHERE id_lokasi != (SELECT id_lokasi FROM model_intensitas_tsunami ORDER BY id_lokasi LIMIT 1)
                    ORDER BY a.geom::geography <-> geom::geography
                    LIMIT 1
                ) b
            ) sub
        """)
        row = db.session.execute(q).fetchone()
        if row:
            print(f"  avg={row.avg_dist:.1f}m, min={row.min_dist:.1f}m, max={row.max_dist:.1f}m")
        
        # Test threshold berbeda
        for thresh in [500, 1000, 2000, 5000]:
            q2 = text(f"""
                SELECT COUNT(DISTINCT b.id_bangunan) as cnt
                FROM (SELECT id_bangunan, geom FROM bangunan_copy LIMIT 500) b
                JOIN LATERAL (
                    SELECT 1 FROM model_intensitas_tsunami r
                    WHERE ST_DWithin(b.geom::geography, r.geom::geography, {thresh})
                    LIMIT 1
                ) n ON TRUE
            """)
            cnt = db.session.execute(q2).scalar()
            print(f"  threshold={thresh}m -> {cnt}/500 bangunan match")

if __name__ == "__main__":
    check()
