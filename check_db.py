import pandas as pd
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        q = """
        SELECT b.id_bangunan, b.kota as kota_b, k.kota as kota_k, k.hsbgn_sederhana
        FROM bangunan_copy b
        LEFT JOIN kota k ON TRIM(LOWER(k.kota)) = TRIM(LOWER(b.kota))
        WHERE b.kota ILIKE '%Badung%' LIMIT 5;
        """
        res = pd.read_sql(text(q), conn)
        print("MATCH TEST:\\n", res)
