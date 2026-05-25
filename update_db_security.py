from app import create_app, db
from app.models import ActivityLog

app = create_app()

with app.app_context():
    db.create_all()
    print("Database updated with ActivityLog model.")
