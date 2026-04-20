from app import create_app
from sqlalchemy import inspect

app = create_app()
with app.app_context():
    inspector = inspect(app.extensions['sqlalchemy'].engine)
    tables = inspector.get_table_names()
    print("Available tables in database:")
    for t in sorted(tables):
        print(f" - {t}")
