from app import create_app,db
from app.models import User, Shift, Attendance
from sqlalchemy import text

app = create_app()

def update_db():
    with app.app_context():
        # Create new tables if they don't exist
        db.create_all()
        
        # Add columns to User table if they don't exist
        with db.engine.connect() as conn:
            # Check for phone column
            try:
                conn.execute(text("SELECT phone FROM user LIMIT 1"))
            except:
                print("Adding phone column to user table")
                conn.execute(text("ALTER TABLE user ADD COLUMN phone VARCHAR(20)"))
            
            # Check for hourly_rate column
            try:
                conn.execute(text("SELECT hourly_rate FROM user LIMIT 1"))
            except:
                print("Adding hourly_rate column to user table")
                conn.execute(text("ALTER TABLE user ADD COLUMN hourly_rate FLOAT DEFAULT 0.0"))

        print("Database updated successfully for Staff Management!")

if __name__ == '__main__':
    update_db()
