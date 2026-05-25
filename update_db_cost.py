from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        with db.engine.connect() as connection:
            connection.execute(text("ALTER TABLE menu_item ADD COLUMN cost REAL DEFAULT 0.0"))
            connection.commit()
            print("Added 'cost' column to menu_item table.")
    except Exception as e:
        print(f"Error (might already exist): {e}")
