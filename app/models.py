from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), default='Customer') # Owner, Manager, Chef, Waiter, Cashier, Customer
    phone = db.Column(db.String(20))
    hourly_rate = db.Column(db.Float, default=0.0)
    loyalty_points = db.Column(db.Integer, default=0)
    
    shifts = db.relationship('Shift', backref='staff', lazy=True)
    attendance = db.relationship('Attendance', backref='staff', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', Role: {self.role})"

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False, default=0.0) # For profit calculation
    image_file = db.Column(db.String(20), nullable=False, default='default_food.jpg')
    category = db.Column(db.String(50), nullable=False, default='Main')
    is_available = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    options = db.Column(db.JSON, nullable=True)

    ingredients = db.relationship('ProductIngredient', backref='menu_item', lazy=True)


    def __repr__(self):
        return f"MenuItem('{self.name}', '${self.price}')"

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_ordered = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(20), nullable=False, default='Pending') # Pending, Preparing, Ready, Completed, Cancelled
    total_price = db.Column(db.Float, nullable=False, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    table_number = db.Column(db.Integer, nullable=True)
    payment_method = db.Column(db.String(20), default='Cash') # Cash, Card, Online
    payment_status = db.Column(db.String(20), default='Unpaid') # Paid, Unpaid, Refunded
    order_type = db.Column(db.String(20), default='Dine-in') # Dine-in, Takeaway, Delivery
    notes = db.Column(db.Text, nullable=True)
    
    # Relationship
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def __repr__(self):
        return f"Order('{self.id}', '{self.status}', Total: {self.total_price})"

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_at_order = db.Column(db.Float, nullable=False) # Store price in case menu changes
    options = db.Column(db.JSON, nullable=True) # Store selected choices: {size: 'M', sugar: '50%'}
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    
    # Relationship to get details easier
    item = db.relationship('MenuItem')

    def __repr__(self):
        return f"OrderItem('{self.item.name}', x{self.quantity})"

class InventoryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=0.0)
    unit = db.Column(db.String(20), nullable=False, default='kg') # kg, liters, pcs
    low_stock_threshold = db.Column(db.Float, default=5.0)
    cost_per_unit = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f"Inventory('{self.name}', '{self.quantity} {self.unit}')"

class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)

    def __repr__(self):
        return f"Supplier('{self.name}')"

class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    total_cost = db.Column(db.Float, default=0.0)
    reference = db.Column(db.String(50)) # Invoice number etc.

    supplier = db.relationship('Supplier', backref='purchases')
    items = db.relationship('PurchaseItem', backref='purchase', lazy=True)

    def __repr__(self):
        return f"Purchase('{self.id}', '{self.date}')"

class PurchaseItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    cost = db.Column(db.Float, nullable=False) # Total cost for this item line

    inventory_item = db.relationship('InventoryItem')

class ProductIngredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_item.id'), nullable=False)
    quantity_required = db.Column(db.Float, nullable=False) # Amount needed for 1 portion

    inventory_item = db.relationship('InventoryItem')
    # Use backref in MenuItem to access ingredients


class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer, unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=4)
    status = db.Column(db.String(20), nullable=False, default='Available') # Available, Occupied, Reserved
    
    reservations = db.relationship('Reservation', backref='table', lazy=True)

    def __repr__(self):
        return f"Table('{self.table_number}', '{self.status}')"

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    party_size = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='Confirmed') # Pending, Confirmed, Cancelled, Completed
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=True) # Assigned table
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"Reservation('{self.name}', '{self.date}', '{self.time}')"

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    notes = db.Column(db.String(200))

    def __repr__(self):
        return f"Shift('{self.user_id}', '{self.date}')"

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    clock_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    clock_out = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default='Present') # Present, Late, Absent, On Leave

    def __repr__(self):
        return f"Attendance('{self.user_id}', '{self.date}', '{self.status}')"

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    discount_value = db.Column(db.Float, nullable=False) # e.g. 10.0 or 0.10
    discount_type = db.Column(db.String(20), default='Percentage') # Percentage, Fixed Amount
    valid_from = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    valid_to = db.Column(db.DateTime, nullable=False)
    usage_limit = db.Column(db.Integer, default=100)
    used_count = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"Coupon('{self.code}', '{self.discount_value}')"

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False) # 1-5
    comment = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship('User', backref='feedback_posts')
    order = db.relationship('Order')

    def __repr__(self):
        return f"Feedback('{self.user_id}', '{self.rating}')"

class CafeSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cafe_name = db.Column(db.String(100), default='Lumina Cafe')
    cafe_logo = db.Column(db.String(100), default='default_logo.png')
    cafe_address = db.Column(db.Text, default='123 Coffee St, Latte City')
    cafe_phone = db.Column(db.String(20), default='')
    cafe_email = db.Column(db.String(120), default='')
    
    # Financials
    tax_rate = db.Column(db.Float, default=0.0) # Percentage
    service_charge = db.Column(db.Float, default=0.0) # Percentage
    currency_symbol = db.Column(db.String(5), default='$')
    
    # Operations
    opening_time = db.Column(db.Time, default=datetime.strptime('08:00', '%H:%M').time())
    closing_time = db.Column(db.Time, default=datetime.strptime('22:00', '%H:%M').time())
    
    # Tech
    printer_ip = db.Column(db.String(50), default='')
    printer_port = db.Column(db.Integer, default=9100)
    POS_enabled = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10), default='en') # en, fr, es...

    # Home Page Content
    hero_title = db.Column(db.String(100), default='Welcome to Our Cafe')
    hero_subtitle = db.Column(db.String(200), default='Experience the best coffee and pastries in town.')
    hero_image = db.Column(db.String(100), default='hero_bg.jpg')
    short_description = db.Column(db.Text, default='We are a cozy cafe dedicated to serving high-quality coffee and artisanal food.')

    # Frontend Management
    theme_color_primary = db.Column(db.String(10), default='#c59d5f') # Gold
    theme_color_primary = db.Column(db.String(10), default='#c59d5f') # Gold
    theme_color_secondary = db.Column(db.String(10), default='#1f1f1f') # Dark
    menu_bg_color = db.Column(db.String(10), default='#f8f9fa') # Light Gray
    card_bg_color = db.Column(db.String(10), default='#ffffff') # White
    text_color = db.Column(db.String(10), default='#333333') # Dark Gray
    
    about_title = db.Column(db.String(100), default='Our Story')
    about_content = db.Column(db.Text, default='Founded in 2024, our cafe has been serving...')
    about_image = db.Column(db.String(100), default='about.jpg')

    # Story & Values
    story_title = db.Column(db.String(100), default='Our Journey')
    story_content = db.Column(db.Text, default='It all started with a bean...')
    story_image = db.Column(db.String(100), default='story.jpg')
    mission_content = db.Column(db.Text, default='To serve the best coffee...')
    vision_content = db.Column(db.Text, default='To be the favorite neighborhood cafe...')
    
    social_facebook = db.Column(db.String(255), default='#')
    social_instagram = db.Column(db.String(255), default='#')
    social_twitter = db.Column(db.String(255), default='#')

    def __repr__(self):
        return f"CafeSetting('{self.cafe_name}')"

class TeamMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    image_file = db.Column(db.String(100), default='default_profile.jpg')
    is_visible = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"TeamMember('{self.name}', '{self.role}')"

class CafePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_file = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(200), nullable=True)
    is_visible = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"CafePhoto('{self.image_file}')"

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), default='general') # order, stock, payment, info
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(255), nullable=True) # URL to redirect to

    def __repr__(self):
        return f"Notification('{self.message}')"

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Nullable for system actions or deleted users
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ip_address = db.Column(db.String(50), nullable=True)

    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True))

    def __repr__(self):
        return f"ActivityLog('{self.action}', '{self.timestamp}')"
