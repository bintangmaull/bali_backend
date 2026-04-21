from app import create_app
from app.extensions import db
from app.models.models_database import TsunamiRiskResults

app = create_app()

def setup_table():
    with app.app_context():
        print("Checking/Creating table tsunami_risk_results...")
        try:
            TsunamiRiskResults.__table__.create(db.engine, checkfirst=True)
            print("Table processed successfully.")
        except Exception as e:
            print(f"Error creating table: {e}")

if __name__ == "__main__":
    setup_table()
