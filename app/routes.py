from flask import Blueprint, render_template, url_for, flash, redirect, request, session
from app import db, bcrypt, limiter
from app.forms import RegistrationForm, LoginForm
from app.models import User, MenuItem, Order, OrderItem, InventoryItem, ProductIngredient, Notification, CafeSetting, Feedback, TeamMember, CafePhoto
from flask_login import login_user, current_user, logout_user, login_required
from urllib.parse import urlparse, urljoin
from datetime import datetime

main = Blueprint('main', __name__)

# Helper function to validate redirect URLs (prevent open redirect attacks)
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == ref_url.netloc

@main.context_processor
def inject_cafe_settings():
    setting = CafeSetting.query.first()
    return dict(cafe_settings=setting)

@main.route("/")
@main.route("/home")
def home():
    settings = CafeSetting.query.first()
    featured_items = MenuItem.query.filter_by(is_featured=True).limit(6).all()
    testimonials = Feedback.query.filter_by(is_public=True).limit(3).all()
    
    
    # Fallback if no specific featured items
    if not featured_items:
        featured_items = MenuItem.query.limit(3).all()

    # Dynamic Content
    team_members = TeamMember.query.filter_by(is_visible=True).all()
    gallery_photos = CafePhoto.query.filter_by(is_visible=True).all()

    return render_template('home.html', title='Home', 
                           featured_items=featured_items, 
                           cafe_settings=settings,
                           testimonials=testimonials,
                           team_members=team_members,
                           gallery_photos=gallery_photos)

@main.route("/menu")
def menu():
    items = MenuItem.query.all()
    # Group items by category
    import collections
    grouped_items = collections.defaultdict(list)
    for item in items:
        grouped_items[item.category].append(item)
    
    # Sort categories by item count (Descending)
    grouped_items = dict(sorted(grouped_items.items(), key=lambda item: len(item[1]), reverse=True))
    
    return render_template('menu.html', title='Menu', grouped_items=grouped_items)

@main.route("/register", methods=['GET', 'POST'])
@limiter.limit("3 per hour")  # Rate limit: max 3 registrations per hour per IP
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Rate limit: max 5 login attempts per minute per IP
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            
            # FIX: Validate redirect URL to prevent open redirect attacks
            if not next_page or not is_safe_url(next_page):
                next_page = url_for('main.home')
            
            return redirect(next_page)
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main.route("/add_to_cart/<int:item_id>")
def add_to_cart(item_id):
    # Fallback for simple add (default options or none)
    return add_to_cart_custom_logic(item_id, request.form)

@main.route("/add_to_cart_custom/<int:item_id>", methods=['POST'])
def add_to_cart_custom(item_id):
    return add_to_cart_custom_logic(item_id, request.form)

def add_to_cart_custom_logic(item_id, form_data):
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    
    # Extract Options
    options = {}
    if 'size' in form_data:
        options['size'] = form_data['size']
    if 'sugar' in form_data:
        options['sugar'] = form_data['sugar']
    if 'addons' in form_data: # Checkbox list
        options['addons'] = request.form.getlist('addons') # Flask specific
        
    # Generate unique key for this item + options combo
    # Simple way: just use uuid for every add, or try to merge?
    # Merging is better UX.
    import json
    import hashlib
    
    # Create a consistent string representation of options for hashing
    opt_str = json.dumps(options, sort_keys=True)
    cart_key = f"{item_id}_{hashlib.md5(opt_str.encode()).hexdigest()}"
    
    if cart_key in cart:
        cart[cart_key]['quantity'] += 1
    else:
        cart[cart_key] = {
            'item_id': item_id,
            'quantity': 1,
            'options': options
        }
    
    session['cart'] = cart
    session.modified = True
    flash('Item added to cart!', 'success')
    return redirect(request.referrer or url_for('main.menu'))

@main.route("/cart")
def view_cart():
    if 'cart' not in session or not session['cart']:
        return render_template('cart.html', title='Cart', cart_items=[], total=0)
    
    cart = session['cart']
    cart_items = []
    total = 0
    
    for key, data in cart.items():
        item = MenuItem.query.get(int(data['item_id']))
        if item:
            item_total = item.price * data['quantity']
            total += item_total
            cart_items.append({
                'key': key,
                'item': item, 
                'quantity': data['quantity'], 
                'options': data['options'],
                'item_total': item_total
            })
    
    return render_template('cart.html', title='Cart', cart_items=cart_items, total=total)

@main.route("/cart/remove/<string:cart_key>")
def remove_from_cart(cart_key):
    cart = session.get('cart', {})
    if cart_key in cart:
        del cart[cart_key]
        session['cart'] = cart
        session.modified = True
        flash('Item removed from cart.', 'info')
    return redirect(url_for('main.view_cart'))

@main.route("/cart/clear")
def clear_cart():
    session.pop('cart', None)
    flash('Cart cleared.', 'info')
    return redirect(url_for('main.menu'))

@main.route("/checkout", methods=['POST'])
@login_required
@limiter.limit("10 per hour")  # Rate limit: max 10 checkouts per hour per user
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('main.menu'))
    
    cart = session['cart']
    total = 0
    order_items_data = []

    # Calculate total and prepare items
    for key, data in cart.items():
        item = MenuItem.query.get(int(data['item_id']))
        if item:
            total += item.price * data['quantity']
            order_items_data.append({
                'item': item, 
                'quantity': data['quantity'],
                'options': data['options']
            })
    
    # Create Order
    order = Order(user_id=current_user.id, total_price=total, status='Pending')
    db.session.add(order)
    db.session.commit() # Commit to get Order ID

    # Create OrderItems
    for entry in order_items_data:
        order_item = OrderItem(order_id=order.id, 
                               menu_item_id=entry['item'].id, 
                               quantity=entry['quantity'],
                               price_at_order=entry['item'].price,
                               options=entry['options'])
        db.session.add(order_item)
        
        # -- Inventory Deduction (Simplified for now - strictly main item ingredients) --
        # Refinement: In real app, add-ons might deduct inventory too.
        ingredients = ProductIngredient.query.filter_by(menu_item_id=entry['item'].id).all()
        for prod_ing in ingredients:
            inventory_item = InventoryItem.query.get(prod_ing.inventory_item_id)
            if inventory_item:
                deduction_amount = prod_ing.quantity_required * entry['quantity']
                inventory_item.quantity -= deduction_amount
                
                if inventory_item.quantity <= inventory_item.low_stock_threshold:
                    stock_msg = f"Low stock alert: {inventory_item.name}"
                    notif = Notification(message=stock_msg, category='stock', link=url_for('admin.manage_inventory'))
                    db.session.add(notif)
    
    # Create Notification for New Order
    new_order_msg = f"New Order #{order.id} placed by {current_user.username} - ${total:.2f}"
    order_notif = Notification(message=new_order_msg, category='order', link=url_for('admin.order_details', order_id=order.id))
    db.session.add(order_notif)

    db.session.commit()
    session.pop('cart', None)
    flash(f'Order #{order.id} placed successfully!', 'success')
    return redirect(url_for('main.home'))

@main.route("/reserve", methods=['GET', 'POST'])
def reserve_table():
    from app.models import Table, Reservation, Notification
    from flask_login import current_user
    
    if request.method == 'POST':
        try:
            # Extract form data
            name = request.form.get('name')
            email = request.form.get('email')
            phone = request.form.get('phone')
            date_str = request.form.get('date')
            time_str = request.form.get('time')
            party_size = int(request.form.get('party_size'))
            notes = request.form.get('notes')

            # Parse DateTime
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            
            # Simple "First Available Table" Logic
            # In a real app, you'd check overlapping time slots logic
            available_table = Table.query.filter(
                Table.capacity >= party_size, 
                Table.status == 'Available'
            ).order_by(Table.capacity.asc()).first()
            
            table_id = available_table.id if available_table else None
            
            # Create Reservation
            reservation = Reservation(
                name=name,
                email=email,
                phone=phone,
                date=date_obj,
                time=time_obj,
                party_size=party_size,
                table_id=table_id,
                notes=notes,
                status='Confirmed' if table_id else 'Pending' # Pending if no table auto-assigned
            )
            
            db.session.add(reservation)
            
            # Notify Admin
            msg = f"New Reservation: {name} for {party_size} people on {date_str} at {time_str}"
            notif = Notification(message=msg, category='info', link=url_for('admin.manage_reservations'))
            db.session.add(notif)
            
            db.session.commit()
            
            flash('Reservation request submitted successfully! We will confirm shortly via email.', 'success')
            return redirect(url_for('main.home'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting reservation: {str(e)}', 'danger')
            return redirect(url_for('main.reserve_table'))

    return render_template('reservation.html', title='Reserve a Table')
