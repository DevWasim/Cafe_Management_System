from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        with db.engine.connect() as connection:
            # Add order_type column
            try:
                connection.execute(text("ALTER TABLE 'order' ADD COLUMN order_type TEXT DEFAULT 'Dine-in'"))
                print("Added 'order_type' column.")
            except Exception as e:
                print(f"Skipping order_type: {e}")

            # Add notes column
            try:
                connection.execute(text("ALTER TABLE 'order' ADD COLUMN notes TEXT"))
                print("Added 'notes' column.")
            except Exception as e:
                print(f"Skipping notes: {e}")
                
            connection.commit()
            print("Database update completed.")
    except Exception as e:
        print(f"Error: {e}")
