
import os
import sys
from sqlalchemy import text
from app.extensions import db
from app.config import Config
from flask import Flask

def get_taxonomy_unique():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print("Unique taxonomy types in bangunan_copy:")
        q = text("SELECT DISTINCT taxonomy FROM bangunan_copy")
        res = db.session.execute(q).fetchall()
        types = [r[0] for r in res]
        print(types)

if __name__ == "__main__":
    get_taxonomy_unique()
