import rasterio
import numpy as np
import requests
from io import BytesIO

BASE_URL = "https://upcxonhddesvrvttvjjt.supabase.co/storage/v1/object/public/geotiff-cogs"

HAZARDS = {
    "earthquake": {
        "rps": ["100", "200", "250", "500", "1000"],
        "pattern": "Earthquake/cog_earthquake_bali_PGA_{}.tif"
    },
    "flood": {
        "rps": ["r2", "r5", "r10", "r25", "r50", "r100", "r250", "rc2", "rc5", "rc10", "rc25", "rc50", "rc100", "rc250"],
        "pattern": "Flood/cog_flood_depth_bali_{}.tif"
    },
    "drought": {
        "rps": ["rp25", "rp50", "rp100", "rp250"],
        "pattern": "Drought/cog_drought_bali_gpm_{}.tif"
    },
    "tsunami": {
        "rps": [""],
        "pattern": "Tsunami/cog_tsunami_bali.tif"
    }
}

def check_raster(url):
    print(f"Checking: {url}")
    try:
        with rasterio.open(url) as src:
            print(f"  Profile: {src.profile}")
            if src.count == 0:
                return "No Bands", "No Bands"
                
            data = src.read(1)
            nodata = src.nodata
            
            # Print unique values if small, or a few samples
            unique = np.unique(data)
            print(f"  Unique values count: {len(unique)}")
            print(f"  Sample unique values: {unique[:20]}")
            
            mask = (data != nodata) if nodata is not None else np.ones(data.shape, dtype=bool)
            
            valid_data = data[mask]
            if len(valid_data) > 0:
                return np.min(valid_data), np.max(valid_data)
            else:
                return "Masked Out", "Masked Out"
    except Exception as e:
        print(f"  Error: {e}")
        return "Error", str(e)

results = []
for h_name, h_info in HAZARDS.items():
    for rp in h_info["rps"]:
        path = h_info["pattern"].format(rp) if "{}" in h_info["pattern"] else h_info["pattern"]
        url = f"{BASE_URL}/{path}"
        min_val, max_val = check_raster(url)
        results.append({
            "hazard": h_name,
            "rp": rp,
            "min": min_val,
            "max": max_val
        })

print("\n--- FINAL RASTER ANALYSIS REPORT ---")
print("{:<12} | {:<8} | {:<12} | {:<12}".format("Hazard", "RP", "Min", "Max"))
print("-" * 55)
for r in results:
    m1 = f"{r['min']:.6f}" if isinstance(r['min'], (float, int)) else str(r['min'])
    m2 = f"{r['max']:.6f}" if isinstance(r['max'], (float, int)) else str(r['max'])
    print("{:<12} | {:<8} | {:<12} | {:<12}".format(r['hazard'], r['rp'], m1, m2))
