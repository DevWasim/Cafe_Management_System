from app import create_app, db
from app.models import CafeSetting, Feedback, MenuItem, User

app = create_app()

with app.app_context():
    # 1. Update Frontend Settings
    setting = CafeSetting.query.first()
    if not setting:
        setting = CafeSetting()
        db.session.add(setting)
    
    # Theme - Let's try a Blue/Dark theme
    setting.theme_color_primary = '#0d6efd' # Bootstrap Blue
    setting.theme_color_secondary = '#212529' # Dark Grey
    
    # Hero (already set, but ensuring)
    setting.hero_title = "Antigravity Frontend Test"
    
    # About
    setting.about_title = "Our Verified Story"
    setting.about_content = "This content is dynamically verified from the admin panel settings."
    setting.about_image = "default_food.jpg" # Reusing existing image for test
    
    # Socials
    setting.social_facebook = "https://facebook.com/antigravity"
    setting.social_instagram = "https://instagram.com/antigravity"
    setting.social_twitter = "https://x.com/antigravity"
    
    db.session.commit()
    print("Frontend test data seeded.")
