
from app.extensions import db
from app.config import Config
from flask import Flask
from sqlalchemy import text

def check():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Kolom di dmg_ratio_tsunami:")
        q = text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'dmg_ratio_tsunami' ORDER BY ordinal_position
        """)
        cols = db.session.execute(q).fetchall()
        for c in cols:
            print(f"  {c.column_name}")
        
        print()
        r1 = db.session.execute(text("SELECT COUNT(*) FROM dmg_ratio_tsunami")).scalar()
        print(f"Jumlah baris di dmg_ratio_tsunami: {r1}")
        
        if r1 and r1 > 0:
            sample = db.session.execute(text("SELECT * FROM dmg_ratio_tsunami LIMIT 3")).fetchall()
            for row in sample:
                print(f"  {dict(row._mapping)}")
            
            # Cek berapa yang nonzero
            cols_q = db.session.execute(text("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'dmg_ratio_tsunami' AND column_name != 'id_lokasi'
            """)).fetchall()
            for c in cols_q:
                col = c.column_name
                cnt = db.session.execute(text(f"SELECT COUNT(*) FROM dmg_ratio_tsunami WHERE {col} > 0")).scalar()
                print(f"  Nonzero in {col}: {cnt}")
        
        print()
        print("Jumlah baris di model_intensitas_tsunami:")
        r2 = db.session.execute(text("SELECT COUNT(*) FROM model_intensitas_tsunami")).scalar()
        print(f"  {r2}")
        
        print()
        print("Sample model_intensitas_tsunami:")
        sample2 = db.session.execute(text("SELECT id_lokasi, inundansi FROM model_intensitas_tsunami LIMIT 5")).fetchall()
        for row in sample2:
            print(f"  {dict(row._mapping)}")

if __name__ == "__main__":
    check()
