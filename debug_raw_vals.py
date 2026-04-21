from app import create_app
from app.service.service_visualisasi_directloss import GedungService
import json

app = create_app()
with app.app_context():
    geojson = GedungService.get_aal_kota_geojson(cv='0.15')
    for f in geojson.get('features', []):
        p = f['properties']
        print(f"City: {p.get('nama_kota')}, AAL_R_TOTAL: {p.get('aal_r_total')}")
