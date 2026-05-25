from app import create_app, db
from app.models import Table

app = create_app()

with app.app_context():
    try:
        db.create_all()
        print("Database tables updated (including Table model if not existed).")
    except Exception as e:
        print(f"Error: {e}")
