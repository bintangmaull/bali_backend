from app import create_app
from app.extensions import db
from app.models.models_database import AALFloodSawahSkema2

def create_skema2_table():
    app = create_app()
    with app.app_context():
        print("Creating table aal_flood_sawah_skema2...")
        AALFloodSawahSkema2.__table__.create(db.engine)
        print("Table created successfully.")

if __name__ == '__main__':
    create_skema2_table()
