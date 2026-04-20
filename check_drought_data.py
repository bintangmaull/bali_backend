
from app import create_app
from app.models.models_database import AALDroughtSawah
from app.extensions import db

app = create_app()
with app.app_context():
    rows = AALDroughtSawah.query.limit(20).all()
    print(f"Total rows in aal_drought_sawah: {AALDroughtSawah.query.count()}")
    for r in rows:
        print(f"City: {r.id_kota}, Year: {r.year}, CC: {r.climate_change}, AAL: {r.aal}")
