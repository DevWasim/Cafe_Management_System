from app import create_app, db
from app.models import CafeSetting, TeamMember, CafePhoto
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Creating new tables for TeamMember and CafePhoto...")
    db.create_all()
    
    print("Updating CafeSetting schema if needed...")
    # SQL to add columns if they don't exist (SQLite doesn't support IF NOT EXISTS for ADD COLUMN easily in one go, so we try/except or inspect)
    # Using raw SQL for SQLite simplicity or just try catch is fine for dev.
    
    commands = [
        "ALTER TABLE cafe_setting ADD COLUMN story_title VARCHAR(100)",
        "ALTER TABLE cafe_setting ADD COLUMN story_content TEXT",
        "ALTER TABLE cafe_setting ADD COLUMN story_image VARCHAR(100)",
        "ALTER TABLE cafe_setting ADD COLUMN mission_content TEXT",
        "ALTER TABLE cafe_setting ADD COLUMN vision_content TEXT"
    ]
    
    for cmd in commands:
        try:
            db.session.execute(text(cmd))
            print(f"Executed: {cmd}")
        except Exception as e:
            # Likely already exists
            print(f"Skipped (probably exists): {cmd}")
            
    db.session.commit()
    print("Database schema update complete.")
