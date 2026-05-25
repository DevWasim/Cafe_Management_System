from app import create_app, db
from app.models import CafeSetting

app = create_app()

with app.app_context():
    # Helper to check and create table if not exists (or just create_all which is safe for existing tables usually, but let's be specific if we can, or just run create_all)
    db.create_all()
    print("Database tables updated.")
    
    # Create default settings if not exists
    if not CafeSetting.query.first():
        default_settings = CafeSetting()
        db.session.add(default_settings)
        db.session.commit()
        print("Default settings created.")
    else:
        print("Settings already exist.")
