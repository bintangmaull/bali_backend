import requests
import json

base_url = 'http://localhost:5000/api'

print("Verifying AAL Skema 2...")
r_aal = requests.get(f"{base_url}/flood-sawah-aal?scheme=2")
if r_aal.ok:
    data = r_aal.json()
    print(f"Return Periods: {data['return_periods']}")
    # Check first item
    if data['data']:
        first = data['data'][0]
        print(f"Sample data for {first['kota']} ({first['year']}):")
        print(f"  PML2: {first.get('pml_2')}, PML5: {first.get('pml_5')}, PML10: {first.get('pml_10')}")
else:
    print(f"AAL fetch failed: {r_aal.status_code}")

print("\nVerifying Direct Loss Skema 2...")
r_dl = requests.get(f"{base_url}/flood-sawah-loss?scheme=2")
if r_dl.ok:
    data = r_dl.json()
    print(f"Return Periods: {data['return_periods']}")
    # Check 'ncc' RP 2
    if 'ncc' in data and '2' in data['ncc']:
        first = data['ncc']['2'][0]
        print(f"Sample Direct Loss for {first['kota']} (RP 2, NCC): {first.get('loss_2022')}")
else:
    print(f"Direct Loss fetch failed: {r_dl.status_code}")
