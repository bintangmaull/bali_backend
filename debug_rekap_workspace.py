import sys
import os

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db
from sqlalchemy import text
import json

app = create_app()
with app.app_context():
    result = db.session.execute(text("SELECT id_kota, dl_exposure FROM rekap_aset_kota LIMIT 1")).fetchone()
    if result:
        print(f"id_kota: {result[0]}")
        print(f"dl_exposure type: {type(result[1])}")
        print(f"dl_exposure: {json.dumps(result[1], indent=2)}")
    else:
        print("No data in rekap_aset_kota")
