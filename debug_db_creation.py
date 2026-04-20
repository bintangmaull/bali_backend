from app import create_app
from app.extensions import db
from sqlalchemy import text, inspect

app = create_app()
with app.app_context():
    print(f"Connected to: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Check if table exists via inspector
    inspector = inspect(db.engine)
    if 'aal_flood_sawah_skema2' in inspector.get_table_names():
        print("Table 'aal_flood_sawah_skema2' ALREADY EXISTS according to inspector.")
    else:
        print("Table 'aal_flood_sawah_skema2' DOES NOT EXIST according to inspector.")
        
    print("Attempting to create table via raw SQL...")
    sql = """
    CREATE TABLE IF NOT EXISTS aal_flood_sawah_skema2 (
        id SERIAL PRIMARY KEY,
        year INTEGER NOT NULL,
        climate_change VARCHAR(10) NOT NULL,
        kota VARCHAR(100) NOT NULL,
        aal DOUBLE PRECISION,
        pml_2 DOUBLE PRECISION DEFAULT 0,
        tvar_2 DOUBLE PRECISION DEFAULT 0,
        pml_5 DOUBLE PRECISION DEFAULT 0,
        tvar_5 DOUBLE PRECISION DEFAULT 0,
        pml_10 DOUBLE PRECISION DEFAULT 0,
        tvar_10 DOUBLE PRECISION DEFAULT 0,
        pml_25 DOUBLE PRECISION DEFAULT 0,
        tvar_25 DOUBLE PRECISION DEFAULT 0,
        pml_50 DOUBLE PRECISION DEFAULT 0,
        tvar_50 DOUBLE PRECISION DEFAULT 0,
        pml_100 DOUBLE PRECISION DEFAULT 0,
        tvar_100 DOUBLE PRECISION DEFAULT 0,
        pml_250 DOUBLE PRECISION DEFAULT 0,
        tvar_250 DOUBLE PRECISION DEFAULT 0
    );
    """
    db.session.execute(text(sql))
    db.session.commit()
    print("SQL command executed and committed.")
    
    # Verify again
    inspector = inspect(db.engine)
    if 'aal_flood_sawah_skema2' in inspector.get_table_names():
        print("Table 'aal_flood_sawah_skema2' NOW EXISTS.")
    else:
        print("Table 'aal_flood_sawah_skema2' STILL DOES NOT EXIST after creation attempt.")
