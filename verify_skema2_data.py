from app import create_app
from app.models.models_database import AALFloodSawahSkema2

app = create_app()
with app.app_context():
    rows = AALFloodSawahSkema2.query.limit(5).all()
    for row in rows:
        print(f"Kota: {row.kota}, Year: {row.year}, AAL: {row.aal:,.2f}, PML10: {row.pml_10:,.2f}")
