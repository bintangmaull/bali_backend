import sys
import os

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db
from app.models.models_database import RekapAsetKota, LossRatioGempa
from sqlalchemy import text
import json

app = create_app()
with app.app_context():
    cities = db.session.query(RekapAsetKota).all()
    
    for city in cities:
        city_name = city.id_kota.upper()
        print(f"Processing city: {city_name}")
        
        # Get ratios for this city from loss_ratio_gempa
        ratios = db.session.query(LossRatioGempa).filter(
            LossRatioGempa.kota == city_name
        ).all()
        
        if not ratios:
            # Try partial match or lowercase if necessary, but Supabase showed all caps
            print(f"  No ratios found for {city_name}")
            continue
            
        # Get current dl_exposure or init empty dict
        dl_exp = city.dl_exposure or {}
        if isinstance(dl_exp, str):
            try:
                dl_exp = json.loads(dl_exp)
            except:
                dl_exp = {}

        # Clean all existing pga_ keys from ANY category to avoid stale absolute values
        for cat in dl_exp.keys():
            if isinstance(dl_exp[cat], dict):
                for k in list(dl_exp[cat].keys()):
                    if k.startswith('pga_'):
                        del dl_exp[cat][k]

        # Ensure main categories exist with correct keys
        # fs = Healthcare, fd = Educational (matching EXPOSURE_GROUPS in frontend)
        categories = ['fs', 'fd', 'electricity', 'airport', 'hotel', 'residential', 'bmn', 'total']
        for cat in categories:
            if cat not in dl_exp:
                dl_exp[cat] = {}
        
        for r in ratios:
            rp = f"pga_{r.return_period}"
            dl_exp['fs'][rp] = r.healthcare_loss_ratio or 0        # fs = Healthcare
            dl_exp['fd'][rp] = r.educational_loss_ratio or 0       # fd = Educational
            dl_exp['electricity'][rp] = r.electricity_loss_ratio or 0
            dl_exp['airport'][rp] = r.airport_loss_ratio or 0
            dl_exp['hotel'][rp] = r.hotel_loss_ratio or 0
            dl_exp['residential'][rp] = r.residential_loss_ratio or 0
            dl_exp['bmn'][rp] = r.bmn_loss_ratio or 0
            
            # Simple average for 'total' city ratio across all handled exposures
            avg_ratio = (
                (r.healthcare_loss_ratio or 0) + (r.educational_loss_ratio or 0) + 
                (r.electricity_loss_ratio or 0) + (r.airport_loss_ratio or 0) + 
                (r.hotel_loss_ratio or 0) + (r.residential_loss_ratio or 0) + 
                (r.bmn_loss_ratio or 0)
            ) / 7.0
            dl_exp['total'][rp] = avg_ratio
            
        # Set dl_exposure
        city.dl_exposure = dl_exp
        
        # Zero out old absolute sum columns for Gempa
        city.dl_sum_pga_100 = 0
        city.dl_sum_pga_200 = 0
        city.dl_sum_pga_250 = 0
        city.dl_sum_pga_500 = 0
        city.dl_sum_pga_1000 = 0
        
        # Preserve or update ratio_pga_* columns as city-wide totals (avg across exposures?)
        # For now, just set them to a representative value or 0 if not needed separately
        # Actually, let's calculate a simple average cross exposure for the summary ratio columns
        for r in ratios:
            avg_city_ratio = (
                (r.healthcare_loss_ratio or 0) + (r.educational_loss_ratio or 0) + 
                (r.electricity_loss_ratio or 0) + (r.airport_loss_ratio or 0) + 
                (r.hotel_loss_ratio or 0) + (r.residential_loss_ratio or 0) + (r.bmn_loss_ratio or 0)
            ) / len(categories)
            if r.return_period == 100: city.ratio_pga_100 = avg_city_ratio
            elif r.return_period == 200: city.ratio_pga_200 = avg_city_ratio
            elif r.return_period == 250: city.ratio_pga_250 = avg_city_ratio
            elif r.return_period == 500: city.ratio_pga_500 = avg_city_ratio
            elif r.return_period == 1000: city.ratio_pga_1000 = avg_city_ratio

    db.session.commit()
    print("Migration completed successfully.")
