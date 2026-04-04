import sys
import os
import json
from sqlalchemy import text

# Add project root to sys.path
sys.path.append('e:/Dashboard/backend-capstone-aal')

from app import create_app
from app.extensions import db
from app.models.models_database import RekapAsetKota, LossRatioGempa
from app.service.service_directloss import recalc_city_directloss_and_aal

app = create_app()

def verify():
    with app.app_context():
        city_name = 'BADUNG'
        print(f"Verifying Gempa rekap fix for city: {city_name}")
        
        # 1. Fetch expected ratios
        expected_ratios = db.session.query(LossRatioGempa).filter(
            LossRatioGempa.kota == city_name
        ).all()
        
        if not expected_ratios:
            print(f"Error: No ratios found in loss_ratio_gempa for {city_name}")
            return

        # 2. Run recalculation
        print(f"Running recalc_city_directloss_and_aal('{city_name}')...")
        recalc_city_directloss_and_aal(city_name)
        
        # 3. Fetch rekap data
        rekap = db.session.query(RekapAsetKota).filter(
            RekapAsetKota.id_kota == city_name
        ).first()
        
        if not rekap:
            print(f"Error: No rekap found for {city_name}")
            return
            
        dl_exp = rekap.dl_exposure
        if isinstance(dl_exp, str):
            dl_exp = json.loads(dl_exp)
            
        print("\n--- Verification Results ---")
        
        # Check if residential and bmn exist
        for cat in ['residential', 'bmn']:
            if cat in dl_exp:
                print(f"✅ Category '{cat}' found in dl_exposure.")
                # Check a specific RP
                rp100 = "100"
                if rp100 in dl_exp[cat]:
                    val = dl_exp[cat][rp100]
                    # Find expected
                    expected = next((r for r in expected_ratios if str(r.return_period) == rp100), None)
                    if expected:
                        expected_val = getattr(expected, f"{cat}_loss_ratio", 0)
                        if abs(val - expected_val) < 1e-9:
                            print(f"  ✅ {cat} RP100 ratio: {val} (Matches expected)")
                        else:
                            print(f"  ❌ {cat} RP100 ratio: {val} (Expected {expected_val})")
            else:
                print(f"❌ Category '{cat}' NOT found in dl_exposure.")

        # Check ratio columns
        print(f"✅ ratio_pga_100: {rekap.ratio_pga_100}")
        print(f"✅ ratio_pga_200: {rekap.ratio_pga_200}")
        
        print("\nVerification process completed.")

if __name__ == "__main__":
    verify()
