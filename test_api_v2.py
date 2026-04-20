import requests
import json

try:
    r = requests.get('http://localhost:5000/api/flood-sawah-aal')
    data = r.json()
    print("KEYS:", data.keys())
    print("\nNCC AAL sample:", data.get('ncc', {}).get('aal', [])[:2])
    print("\nCC AAL sample:", data.get('cc', {}).get('aal', [])[:2])
    print("\nRPs:", data.get('return_periods', []))
    print("\nNCC RP 10 sample:", data.get('ncc', {}).get('10', [])[:2])
except Exception as e:
    print("ERROR:", e)
