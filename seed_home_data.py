from app import create_app, db
from app.models import Feedback, MenuItem, User, CafeSetting
from datetime import datetime

app = create_app()

with app.app_context():
    # 1. Update Settings
    setting = CafeSetting.query.first()
    if not setting:
        setting = CafeSetting()
        db.session.add(setting)
    
    setting.hero_title = "Welcome to Antigravity"
    setting.hero_subtitle = "Where Code Meets Caffeine"
    setting.short_description = "The best place to code, sip, and relax."
    
    # 2. Mark a Menu Item as Featured
    item = MenuItem.query.first()
    if item:
        item.is_featured = True
        print(f"Marked '{item.name}' as featured.")
    
    # 3. Create/Update Feedback
    user = User.query.first()
    if user:
        f1 = Feedback(user_id=user.id, rating=5, comment="Amazing coffee!", is_public=True)
        f2 = Feedback(user_id=user.id, rating=4, comment="Great atmosphere, but crowded.", is_public=False)
        db.session.add(f1)
        db.session.add(f2)
        print("Feedback added.")
    
    db.session.commit()
    print("Seeding complete.")
