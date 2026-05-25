from app import create_app, db
from app.models import Notification

app = create_app()

with app.app_context():
    db.create_all()
    print("Database updated with Notification model.")
