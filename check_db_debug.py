import os
import sys
# Add current directory to path
sys.path.append(os.path.abspath(os.curdir))

from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()
with app.app_context():
    try:
        res = db.session.execute(text('SELECT count(*) FROM loss_flood_sawah')).scalar()
        print(f'Rows in loss_flood_sawah: {res}')
        
        if res > 0:
            res2 = db.session.execute(text('SELECT * FROM loss_flood_sawah LIMIT 1')).fetchone()
            print(f'Sample row: {res2}')
            
            # Check for a specific city
            res3 = db.session.execute(text("SELECT count(*) FROM loss_flood_sawah WHERE kota ILIKE 'BADUNG'")).scalar()
            print(f'Rows for BADUNG: {res3}')
    except Exception as e:
        print(f'Error querying table: {e}')
