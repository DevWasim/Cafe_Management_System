from app import create_app,db
from app.models import User, Coupon, Feedback
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Create tables for new models
    try:
        db.create_all()
        print("Database tables created (if they didn't exist).")
    except Exception as e:
        print(f"Error creating tables: {e}")

    # Add loyalty_points column to User if it doesn't exist
    try:
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE user ADD COLUMN loyalty_points INTEGER DEFAULT 0"))
            print("Added 'loyalty_points' column to 'user' table.")
    except Exception as e:
        print(f"Column 'loyalty_points' might already exist or other error: {e}")
        
    print("Database update for Customer Management features completed.")
