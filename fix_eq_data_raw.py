import sys
import os
import json
import psycopg2
from sqlalchemy import text

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db

app = create_app()

def fix_it():
    with app.app_context():
        print("Starting robust data fix...")
        
        # 1. Get all ratios from loss_ratio_gempa
        ratios = db.session.execute(text("SELECT * FROM loss_ratio_gempa")).fetchall()
        ratio_map = {}
        for r in ratios:
            # Assuming columns: id, kota, return_period, airport, educational, electricity, healthcare, hotel, residential, bmn
            # We match by kota name
            kota = r.kota.upper()
            rp = r.return_period
            if kota not in ratio_map: ratio_map[kota] = {}
            ratio_map[kota][rp] = {
                'airport': r.airport_loss_ratio or 0,
                'educational': r.educational_loss_ratio or 0,
                'electricity': r.electricity_loss_ratio or 0,
                'healthcare': r.healthcare_loss_ratio or 0,
                'hotel': r.hotel_loss_ratio or 0,
                'residential': r.residential_loss_ratio or 0,
                'bmn': r.bmn_loss_ratio or 0
            }
        
        print(f"Loaded ratios for {len(ratio_map)} cities.")

        # 2. Get all cities from rekap_aset_kota
        cities = db.session.execute(text("SELECT id_kota, dl_exposure FROM rekap_aset_kota")).fetchall()
        
        for city_id, dl_exp_raw in cities:
            print(f"Processing {city_id}...")
            dl_exp = dl_exp_raw or {}
            if isinstance(dl_exp, str):
                try: dl_exp = json.loads(dl_exp)
                except: dl_exp = {}
            
            # CLEAR ALL STALE PGA DATA
            for cat in list(dl_exp.keys()):
                if isinstance(dl_exp[cat], dict):
                    for k in list(dl_exp[cat].keys()):
                        if k.startswith('pga_'):
                            del dl_exp[cat][k]

            # MATCH RATIOS
            city_ratios = ratio_map.get(city_id.upper())
            if not city_ratios:
                print(f"  Warning: No ratios found for {city_id}")
            else:
                # fs=Healthcare, fd=Educational (matching EXPOSURE_GROUPS in frontend)
                categories = ['fs', 'fd', 'electricity', 'airport', 'hotel', 'residential', 'bmn']
                for rp, cats in city_ratios.items():
                    rp_key = f"pga_{rp}"
                    total_ratio_sum = 0
                    cat_map = {
                        'fs': cats.get('healthcare', 0),        # fs = Healthcare Facilities
                        'fd': cats.get('educational', 0),       # fd = Educational Facilities
                        'electricity': cats.get('electricity', 0),
                        'airport': cats.get('airport', 0),
                        'hotel': cats.get('hotel', 0),
                        'residential': cats.get('residential', 0),
                        'bmn': cats.get('bmn', 0)
                    }
                    for cat, val in cat_map.items():
                        if cat not in dl_exp: dl_exp[cat] = {}
                        dl_exp[cat][rp_key] = val
                        total_ratio_sum += val
                    
                    if 'total' not in dl_exp: dl_exp['total'] = {}
                    dl_exp['total'][rp_key] = total_ratio_sum / len(categories)
            
            # UPDATE DB USING RAW SQL
            db.session.execute(
                text("UPDATE rekap_aset_kota SET dl_exposure = :json_data WHERE id_kota = :id_kota"),
                {"json_data": json.dumps(dl_exp), "id_kota": city_id}
            )
        
        db.session.commit()
        print("COMMIT SUCCESSFUL.")

if __name__ == "__main__":
    fix_it()
