from app import create_app, db
from app.models import CafeSetting, MenuItem, Feedback
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Use raw SQL to add columns if not using migration tool (simple approach for dev)
    # SQLite doesn't support generic ADD COLUMN well with SQLAlchemy create_all if table exists.
    # But since we are in dev, we can enforce manual alter or just rely on 'create_all' not doing alter.
    # Recommendation: create a function to manually alter table for SQLite.
    pass

    # Actually, create_all does NOT alter existing tables.
    # I will stick to the manual ALTER TABLE approach for SQLite.
    
    with db.engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN hero_title VARCHAR(100) DEFAULT 'Welcome to Our Cafe'"))
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN hero_subtitle VARCHAR(200) DEFAULT 'Experience the best coffee and pastries in town.'"))
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN hero_image VARCHAR(100) DEFAULT 'hero_bg.jpg'"))
            conn.execute(text("ALTER TABLE cafe_setting ADD COLUMN short_description TEXT DEFAULT 'We are a cozy cafe dedicated to serving high-quality coffee and artisanal food.'"))
            print("CafeSetting updated.")
        except Exception as e:
            print(f"CafeSetting update skipped/error: {e}")

        try:
            conn.execute(text("ALTER TABLE menu_item ADD COLUMN is_featured BOOLEAN DEFAULT 0"))
            print("MenuItem updated.")
        except Exception as e:
            print(f"MenuItem update skipped/error: {e}")

        try:
            conn.execute(text("ALTER TABLE feedback ADD COLUMN is_public BOOLEAN DEFAULT 0"))
            print("Feedback updated.")
        except Exception as e:
            print(f"Feedback update skipped/error: {e}")
            
        conn.commit()
