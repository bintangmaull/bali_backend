import json
from app import create_app
from app.service.service_visualisasi_directloss import GedungService

app = create_app()
with app.app_context():
    # Test with CV 0.15
    print("Testing CV 0.15...")
    geojson = GedungService.get_aal_kota_geojson(cv='0.15')
    
    if not geojson:
        print("GeoJSON is NONE!")
    else:
        cities_with_data = []
        for f in geojson.get('features', []):
            props = f['properties']
            city = props.get('id_kota') or props.get('nama_kota')
            aal_r = props.get('aal_r_total')
            aal_rc = props.get('aal_rc_total')
            if (aal_r and aal_r > 0) or (aal_rc and aal_rc > 0):
                cities_with_data.append((city, aal_r, aal_rc))
                
        print(f"Total features: {len(geojson.get('features', []))}")
        print(f"Cities with building AAL > 0: {cities_with_data}")

        # Inspect one feature props
        if geojson.get('features'):
            print("Sample props (Badung):")
            badung = next((f for f in geojson['features'] if 'BADUNG' in (f['properties'].get('id_kota') or '').upper()), None)
            if badung:
                print(json.dumps(badung['properties'], indent=2))
            else:
                print("Badung not found in GeoJSON")
