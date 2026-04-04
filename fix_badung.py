import sys
import os

# Add backend dir to sys.path
sys.path.append(r"e:\Dashboard\backend-capstone-aal")

from app.extensions import db
from app.service.service_directloss import recalc_city_rekap_only
import app.main

app_instance = app.main.app
with app_instance.app_context():
    print("Memperbaiki data Badung di database...")
    try:
        recalc_city_rekap_only('Badung')
        print("Data Badung berhasil diperbaiki!")
    except Exception as e:
        print(f"Error: {e}")
