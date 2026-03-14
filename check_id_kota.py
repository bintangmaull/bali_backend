
import os
import sys
from sqlalchemy import text
from app.extensions import db
from app.config import Config
from flask import Flask

def check_aal_data():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Checking first row of hasil_aal_kota...")
        q = text("SELECT id_kota FROM hasil_aal_kota LIMIT 1")
        res = db.session.execute(q).fetchone()
        if res:
            print(f"Value of id_kota: {res[0]}")
        else:
            print("Table is empty.")

if __name__ == "__main__":
    check_aal_data()
