from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN theme_color_primary VARCHAR(10) DEFAULT '#c59d5f'"))
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN theme_color_secondary VARCHAR(10) DEFAULT '#1f1f1f'"))
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN about_title VARCHAR(100) DEFAULT 'Our Story'"))
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN about_content TEXT DEFAULT 'Founded in 2024, our cafe has been serving...'"))
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN about_image VARCHAR(100) DEFAULT 'about.jpg'"))
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN social_facebook VARCHAR(255) DEFAULT '#'"))
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN social_instagram VARCHAR(255) DEFAULT '#'"))
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN social_twitter VARCHAR(255) DEFAULT '#'"))
            print("CafeSetting updated for Frontend Management.")
        except Exception as e:
            print(f"Update error/skipped: {e}")
            
        conn.commit()
