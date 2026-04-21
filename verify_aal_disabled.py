import sys
import os
from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models.models_database import HasilAALProvinsi, HasilProsesDirectLoss
from app.service.service_directloss import recalc_city_directloss_and_aal

app = create_app()
with app.app_context():
    kota = 'GIANYAR'
    
    # 1. Get AAL values before
    aal_before = db.session.query(HasilAALProvinsi).filter_by(id_kota=kota).one()
    aal_val_before = aal_before.aal_pga_total
    print(f"BEFORE AAL: {aal_val_before}")
    
    # 2. Get some Direct Loss value before
    # We'll just check if the function runs and completes
    print("Running recalc_city_directloss_and_aal...")
    res = recalc_city_directloss_and_aal(kota)
    print(f"Result: {res}")
    
    # 3. Get AAL values after
    aal_after = db.session.query(HasilAALProvinsi).filter_by(id_kota=kota).one()
    aal_val_after = aal_after.aal_pga_total
    print(f"AFTER AAL: {aal_val_after}")
    
    if aal_val_before == aal_val_after:
        print("SUCCESS: AAL remained unchanged.")
    else:
        print(f"FAILURE: AAL changed from {aal_val_before} to {aal_val_after}")
        print(f"Diff: {aal_val_after - aal_val_before}")
