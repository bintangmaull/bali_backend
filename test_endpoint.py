
import requests
try:
    r = requests.get('http://127.0.0.1:5000/api/aal-drought-all-cities')
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Total rows: {len(data)}")
        if len(data) > 0:
            print(f"Sample city: {data[0].get('id_kota')}")
    else:
        print(f"Response: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
