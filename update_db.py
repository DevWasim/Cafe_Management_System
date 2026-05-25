from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if column exists first to avoid error
        with db.engine.connect() as connection:
            # SQLite syntax for adding column.
            # Note: JSON type in SQLite becomes TEXT or similar handled by SQLAlchemy
            connection.execute(text("ALTER TABLE menu_item ADD COLUMN options TEXT"))
            connection.commit()
            print("Successfully added 'options' column to menu_item table.")
    except Exception as e:
        print(f"Error (might already exist): {e}")
