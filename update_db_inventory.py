from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        with db.engine.connect() as connection:
            # 1. Update InventoryItem table
            try:
                connection.execute(text("ALTER TABLE inventory_item ADD COLUMN cost_per_unit FLOAT DEFAULT 0.0"))
                print("Added 'cost_per_unit' to inventory_item.")
            except Exception as e:
                print(f"Skipping inventory_item update: {e}")

            # 2. Create Supplier table
            try:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS supplier (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        contact_name VARCHAR(100),
                        email VARCHAR(120),
                        phone VARCHAR(20),
                        address TEXT
                    )
                """))
                print("Created 'supplier' table.")
            except Exception as e:
                print(f"Error creating supplier: {e}")

            # 3. Create Purchase table
            try:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS purchase (
                        id INTEGER PRIMARY KEY,
                        date DATETIME NOT NULL,
                        supplier_id INTEGER,
                        total_cost FLOAT DEFAULT 0.0,
                        reference VARCHAR(50),
                        FOREIGN KEY(supplier_id) REFERENCES supplier(id)
                    )
                """))
                print("Created 'purchase' table.")
            except Exception as e:
                print(f"Error creating purchase: {e}")

            # 4. Create PurchaseItem table
            try:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS purchase_item (
                        id INTEGER PRIMARY KEY,
                        purchase_id INTEGER NOT NULL,
                        inventory_item_id INTEGER NOT NULL,
                        quantity FLOAT NOT NULL,
                        cost FLOAT NOT NULL,
                        FOREIGN KEY(purchase_id) REFERENCES purchase(id),
                        FOREIGN KEY(inventory_item_id) REFERENCES inventory_item(id)
                    )
                """))
                print("Created 'purchase_item' table.")
            except Exception as e:
                print(f"Error creating purchase_item: {e}")

            # 5. Create ProductIngredient table
            try:
                connection.execute(text("""
                    CREATE TABLE IF NOT EXISTS product_ingredient (
                        id INTEGER PRIMARY KEY,
                        menu_item_id INTEGER NOT NULL,
                        inventory_item_id INTEGER NOT NULL,
                        quantity_required FLOAT NOT NULL,
                        FOREIGN KEY(menu_item_id) REFERENCES menu_item(id),
                        FOREIGN KEY(inventory_item_id) REFERENCES inventory_item(id)
                    )
                """))
                print("Created 'product_ingredient' table.")
            except Exception as e:
                print(f"Error creating product_ingredient: {e}")

            connection.commit()
            print("Database inventory update completed successfully.")

    except Exception as e:
        print(f"Critical Error: {e}")
