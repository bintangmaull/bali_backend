import requests
r = requests.get('http://localhost:5000/api/flood-sawah-aal')
d = r.json()
print("KEYS:", d.keys())
print("SAMPLE 0:", d['data'][0])
print("TOTAL ROWS:", len(d['data']))
