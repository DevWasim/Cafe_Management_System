from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed Admin
        from app.models import User, MenuItem
        from app import bcrypt
        if not User.query.filter_by(username='admin').first():
            hashed_pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(username='admin', email='admin@cafe.com', password=hashed_pw, is_admin=True, role='Owner')
            db.session.add(admin)
            
            # Seed Sample Menu Items (if empty)
            if not MenuItem.query.first():
                item1 = MenuItem(name='Espresso', description='Strong black coffee', price=3.50, category='Coffee', image_file='default_food.jpg')
                item2 = MenuItem(name='Croissant', description='Buttery pastry', price=4.00, category='Snacks', image_file='default_food.jpg')
                db.session.add_all([item1, item2])
            
            db.session.commit()
            print("Database seeded!")
    app.run(debug=True)
