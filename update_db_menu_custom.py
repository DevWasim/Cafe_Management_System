from app import create_app,db
from app.models import OrderItem, CafeSetting
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Updating database schema...")
    
    # 1. Add options column to OrderItem if not exists
    try:
        with db.engine.connect() as connection:
            connection.execute(text("ALTER TABLE order_item ADD COLUMN options JSON"))
            print("Added 'options' column to order_item table.")
    except Exception as e:
        print(f"Column 'options' might already exist or error: {e}")

    # 2. Add new color columns to CafeSetting if not exists
    new_cols = {
        'menu_bg_color': "VARCHAR(10) DEFAULT '#f8f9fa'",
        'card_bg_color': "VARCHAR(10) DEFAULT '#ffffff'",
        'text_color': "VARCHAR(10) DEFAULT '#333333'"
    }

    for col_name, col_def in new_cols.items():
        try:
            with db.engine.connect() as connection:
                connection.execute(text(f"ALTER TABLE cafe_setting ADD COLUMN {col_name} {col_def}"))
                print(f"Added '{col_name}' column to cafe_setting table.")
        except Exception as e:
            print(f"Column '{col_name}' might already exist or error: {e}")
            
    db.session.commit()
    print("Database schema update complete.")
