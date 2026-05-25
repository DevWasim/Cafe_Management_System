from app import create_app, db
from app.models import Notification

app = create_app()

with app.app_context():
    # 1. New Order Notification
    n1 = Notification(message="New Order #999 placed by Test User - $50.00", category='order', link='/admin/orders')
    db.session.add(n1)
    
    # 2. Low Stock Notification
    n2 = Notification(message="Low stock alert: Coffee Beans is down to 2.5 kg", category='stock', link='/admin/inventory')
    db.session.add(n2)
    
    # 3. Payment Notification
    n3 = Notification(message="Payment Confirmed / Order Completed: Order #888", category='payment', link='/admin/orders')
    db.session.add(n3)
    
    db.session.commit()
    print("Test notifications created.")
