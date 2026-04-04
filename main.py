import os
from app import create_app
from app.extensions import db  # Pastikan import db dari extensions
from flask_migrate import Migrate  # Penting untuk Flask-Migrate

app = create_app()

# Inisialisasi Flask-Migrate
migrate = Migrate(app, db)  # <== TANPA INI, `flask db` TIDAK AKAN KENAL

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
