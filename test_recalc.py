import sys
import pandas as pd
from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models.models_database import HasilAALProvinsi
from app.service.service_directloss import recalc_city_directloss_and_aal

app = create_app()
with app.app_context():
    kota = 'GIANYAR'
    
    # 1. Cek nilai gempa sebelum
    row1 = db.session.query(HasilAALProvinsi).filter_by(id_kota=kota).one()
    print("BEFORE Gempa AAL Total:", row1.aal_pga_total)
    
    # 2. Recalc
    res = recalc_city_directloss_and_aal(kota)
    print("Recalc Response:", res)
    
    # 3. Cek nilai gempa sesudah
    row2 = db.session.query(HasilAALProvinsi).filter_by(id_kota=kota).one()
    print("AFTER Gempa AAL Total:", row2.aal_pga_total)
    print("DIFF:", row2.aal_pga_total - row1.aal_pga_total)
