import sys
import os

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.repository.repo_visualisasi_directloss import GedungRepository
import json

app = create_app()
with app.app_context():
    result = GedungRepository.fetch_rekap_aset_kota_geojson()
    print("Keys in result:", result.keys())
    if 'provincial_gempa_loss_ratios' in result:
        print("Provincial aggregate found!")
        print(json.dumps(result['provincial_gempa_loss_ratios'], indent=2)[:500])
    
    if result['features']:
        feat = result['features'][0]
        print(f"Feature properties for {feat['properties'].get('nama_kota')}:")
        print(json.dumps(feat['properties'].get('dl_exposure'), indent=2)[:500])
