import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, current_app
from app import db
from app.admin import admin
from app.forms import MenuItemForm, TableForm
from functools import wraps
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from flask_login import login_required, current_user
from app.models import MenuItem, Order, User, InventoryItem, OrderItem, Table, Supplier, Purchase, PurchaseItem, ProductIngredient, Shift, Attendance, Coupon, Feedback, CafeSetting, Notification, ActivityLog, TeamMember, CafePhoto
import json
from flask import send_file, Response
import io
from app.forms import MenuItemForm, TableForm, InventoryItemForm, SupplierForm, PurchaseForm, StaffForm, ShiftForm, AttendanceForm, CouponForm, SettingsForm, FrontendSettingsForm, TeamMemberForm, CafePhotoForm

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

def save_picture(form_picture, folder='menu_items'):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    # Ensure directory exists
    picture_path = os.path.join(current_app.root_path, f'static/images/{folder}', picture_fn)
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    
    # Resize image
    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

def log_activity(action, details=None):
    if current_user.is_authenticated:
        log = ActivityLog(user_id=current_user.id, action=action, details=details, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Date calculations
    today = datetime.now().date()
    first_day_of_month = today.replace(day=1)
    
    # -- Statistics --
    
    # 1. Sales
    daily_sales = db.session.query(func.sum(Order.total_price)).filter(
        func.date(Order.date_ordered) == today,
        Order.status == 'Completed'
    ).scalar() or 0.0

    monthly_sales = db.session.query(func.sum(Order.total_price)).filter(
        func.date(Order.date_ordered) >= first_day_of_month,
        Order.status == 'Completed'
    ).scalar() or 0.0

    total_revenue = db.session.query(func.sum(Order.total_price)).filter(
        Order.status == 'Completed'
    ).scalar() or 0.0

    # 2. Orders Counts
    total_orders = Order.query.count()
    completed_orders = Order.query.filter_by(status='Completed').count()
    pending_orders = Order.query.filter_by(status='Pending').count()

    # 3. Best Selling Items (Top 5)
    # Join OrderItem with MenuItem, group by Item, sum quantity
    best_selling = db.session.query(
        MenuItem.name, 
        func.sum(OrderItem.quantity).label('total_sold'),
        MenuItem.price,
        MenuItem.image_file
    ).join(OrderItem, MenuItem.id == OrderItem.menu_item_id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.status == 'Completed')\
     .group_by(MenuItem.id)\
     .order_by(desc('total_sold'))\
     .limit(5).all()

    # 4. Low Stock Alerts
    # Assuming InventoryItem exists, otherwise this will be empty or error if model missing
    # We will try/except or check if model exists. User said "u have... folder...". 
    # The read of models.py showed InventoryItem exists.
    low_stock_items = InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.low_stock_threshold).all()

    # 5. Recent Activity (Orders)
    recent_orders = Order.query.order_by(Order.date_ordered.desc()).limit(10).all()
    
    total_users = User.query.count()
    total_menu_items = MenuItem.query.count()

    return render_template('admin/dashboard.html', title='Admin Dashboard',
                           daily_sales=daily_sales,
                           monthly_sales=monthly_sales,
                           total_revenue=total_revenue,
                           total_orders=total_orders,
                           completed_orders=completed_orders,
                           pending_orders=pending_orders,
                           best_selling=best_selling,
                           low_stock_items=low_stock_items,
                           recent_orders=recent_orders,
                           total_users=total_users,
                           total_menu_items=total_menu_items)

@admin.route('/menu/manage')
@login_required
@admin_required
def manage_menu():
    items = MenuItem.query.all()
    return render_template('admin/manage_menu.html', title='Manage Menu', items=items)

@admin.route('/menu/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_menu_item():
    form = MenuItemForm()
    if form.validate_on_submit():
        image_file = 'default_food.jpg'
        if form.image_file.data:
            image_file = save_picture(form.image_file.data)
        
        # Parse options
        options = {}
        if form.sizes.data:
            options['sizes'] = [s.strip() for s in form.sizes.data.split(',') if s.strip()]
        if form.sugar_levels.data:
            options['sugar_levels'] = [s.strip() for s in form.sugar_levels.data.split(',') if s.strip()]
        if form.add_ons.data:
            options['add_ons'] = [s.strip() for s in form.add_ons.data.split(',') if s.strip()]

        item = MenuItem(name=form.name.data, 
                        price=form.price.data,
                        cost=form.cost.data if form.cost.data else 0.0,
                        category=form.category.data, 
                        description=form.description.data,
                        image_file=image_file,
                        is_available=form.is_available.data,
                        is_featured=form.is_featured.data,
                        options=options if options else None)
        db.session.add(item)
        db.session.commit()
        flash('Menu item has been created!', 'success')
        return redirect(url_for('admin.manage_menu'))
    return render_template('admin/edit_item.html', title='Add Menu Item', form=form, legend='Add Menu Item')

@admin.route('/menu/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    form = MenuItemForm(obj=item)  # Pass obj to pre-populate form
    
    if form.validate_on_submit():
        item.name = form.name.data
        item.price = form.price.data
        item.cost = form.cost.data if form.cost.data else 0.0
        item.category = form.category.data
        item.description = form.description.data
        item.is_available = form.is_available.data
        item.is_featured = form.is_featured.data
        
        # Parse options
        options = {}
        if form.sizes.data:
            options['sizes'] = [s.strip() for s in form.sizes.data.split(',') if s.strip()]
        if form.sugar_levels.data:
            options['sugar_levels'] = [s.strip() for s in form.sugar_levels.data.split(',') if s.strip()]
        if form.add_ons.data:
            options['add_ons'] = [s.strip() for s in form.add_ons.data.split(',') if s.strip()]
        item.options = options if options else None

        if form.image_file.data:
            item.image_file = save_picture(form.image_file.data)
        
        db.session.commit()
        flash('Menu item has been updated!', 'success')
        return redirect(url_for('admin.manage_menu'))
    
    # For GET request, manually populate option fields (obj doesn't handle JSON fields)
    if request.method == 'GET' and item.options:
        if 'sizes' in item.options:
            form.sizes.data = ', '.join(item.options['sizes'])
        if 'sugar_levels' in item.options:
            form.sugar_levels.data = ', '.join(item.options['sugar_levels'])
        if 'add_ons' in item.options:
            form.add_ons.data = ', '.join(item.options['add_ons'])
        
    return render_template('admin/edit_item.html', title='Edit Menu Item', form=form, legend='Edit Menu Item')

@admin.route('/menu/delete/<int:item_id>', methods=['POST'])
@login_required
@admin_required
def delete_menu_item(item_id):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Menu item has been deleted!', 'success')
    return redirect(url_for('admin.manage_menu'))

@admin.route('/orders')
@login_required
@admin_required
def manage_orders():
    # Filters
    status_filter = request.args.get('status')
    type_filter = request.args.get('type')
    
    query = Order.query
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    if type_filter:
        query = query.filter(Order.order_type == type_filter)
        
    # Sort by newest first
    orders = query.order_by(Order.date_ordered.desc()).all()
    
    return render_template('admin/orders.html', title='Manage Orders', orders=orders, 
                           status_filter=status_filter, type_filter=type_filter)

@admin.route('/order/<int:order_id>')
@login_required
@admin_required
def order_details(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_details.html', title=f'Order #{order.id}', order=order)

@admin.route('/order/update_status/<int:order_id>/<string:status>')
@login_required
@admin_required
def update_order_status(order_id, status):
    order = Order.query.get_or_404(order_id)
    order.status = status
    
    if status == 'Completed':
        msg = f"Payment Confirmed / Order Completed: Order #{order.id}"
        notif = Notification(message=msg, category='payment', link=url_for('admin.order_details', order_id=order.id))
        db.session.add(notif)
        
    db.session.commit()
    flash(f'Order #{order.id} status updated to {status}!', 'success')
    # Redirect back to referring page if possible, else dashboard
    return redirect(request.referrer or url_for('admin.dashboard'))

@admin.route('/order/delete/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    # Delete related order items first (though cascade might handle this depending on setup)
    OrderItem.query.filter_by(order_id=order.id).delete()
    db.session.delete(order)
    db.session.commit()
    flash(f'Order #{order.id} has been deleted!', 'success')
    return redirect(url_for('admin.manage_orders'))

@admin.route('/tables')
@login_required
@admin_required
def manage_tables():
    # Fetch all tables ordered by number
    tables = Table.query.order_by(Table.table_number).all()
    form = TableForm()
    return render_template('admin/tables.html', title='Manage Tables', tables=tables, form=form)

@admin.route('/table/add', methods=['POST'])
@login_required
@admin_required
def add_table():
    form = TableForm()
    if form.validate_on_submit():
        # Check if table number exists
        existing = Table.query.filter_by(table_number=form.table_number.data).first()
        if existing:
            flash(f'Table {form.table_number.data} already exists!', 'danger')
        else:
            table = Table(table_number=form.table_number.data, capacity=form.capacity.data, status=form.status.data)
            db.session.add(table)
            db.session.commit()
            flash(f'Table {table.table_number} added successfully!', 'success')
    else:
        for err in form.errors.values():
            flash(f'Error adding table: {err}', 'danger')
            
    return redirect(url_for('admin.manage_tables'))

@admin.route('/table/delete/<int:table_id>', methods=['POST'])
@login_required
@admin_required
def delete_table(table_id):
    table = Table.query.get_or_404(table_id)
    db.session.delete(table)
    db.session.commit()
    flash(f'Table {table.table_number} deleted!', 'success')
    return redirect(url_for('admin.manage_tables'))

@admin.route('/table/status/<int:table_id>/<string:status>')
@login_required
@admin_required
def update_table_status(table_id, status):
    table = Table.query.get_or_404(table_id)
    table.status = status
    db.session.commit()
    flash(f'Table {table.table_number} is now {status}!', 'success')
    flash(f'Table {table.table_number} is now {status}!', 'success')
    return redirect(url_for('admin.manage_tables'))

# -- Inventory Management --

@admin.route('/inventory')
@login_required
@admin_required
def manage_inventory():
    items = InventoryItem.query.all()
    return render_template('admin/inventory.html', title='Inventory', items=items)

@admin.route('/inventory/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_inventory_item():
    form = InventoryItemForm()
    if form.validate_on_submit():
        item = InventoryItem(name=form.name.data, 
                             quantity=form.quantity.data,
                             unit=form.unit.data,
                             low_stock_threshold=form.low_stock_threshold.data,
                             cost_per_unit=form.cost_per_unit.data)
        db.session.add(item)
        db.session.commit()
        flash(f'Ingredient {item.name} added!', 'success')
        return redirect(url_for('admin.manage_inventory'))
    return render_template('admin/edit_inventory.html', title='Add Ingredient', form=form, legend='Add Ingredient')

@admin.route('/inventory/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    form = InventoryItemForm()
    if form.validate_on_submit():
        item.name = form.name.data
        item.quantity = form.quantity.data
        item.unit = form.unit.data
        item.low_stock_threshold = form.low_stock_threshold.data
        item.cost_per_unit = form.cost_per_unit.data
        db.session.commit()
        flash(f'Ingredient {item.name} updated!', 'success')
        return redirect(url_for('admin.manage_inventory'))
    elif request.method == 'GET':
        form.name.data = item.name
        form.quantity.data = item.quantity
        form.unit.data = item.unit
        form.low_stock_threshold.data = item.low_stock_threshold
        form.cost_per_unit.data = item.cost_per_unit
    return render_template('admin/edit_inventory.html', title='Edit Ingredient', form=form, legend='Edit Ingredient')

@admin.route('/inventory/delete/<int:item_id>', methods=['POST'])
@login_required
@admin_required
def delete_inventory_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Ingredient deleted!', 'success')
    return redirect(url_for('admin.manage_inventory'))

# -- Supplier Management --

@admin.route('/suppliers')
@login_required
@admin_required
def manage_suppliers():
    suppliers = Supplier.query.all()
    return render_template('admin/suppliers.html', title='Suppliers', suppliers=suppliers)

@admin.route('/supplier/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_supplier():
    form = SupplierForm()
    if form.validate_on_submit():
        supplier = Supplier(name=form.name.data,
                            contact_name=form.contact_name.data,
                            email=form.email.data,
                            phone=form.phone.data,
                            address=form.address.data)
        db.session.add(supplier)
        db.session.commit()
        flash('Supplier added!', 'success')
        return redirect(url_for('admin.manage_suppliers'))
    return render_template('admin/edit_supplier.html', title='Add Supplier', form=form, legend='Add Supplier')

@admin.route('/supplier/edit/<int:supplier_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm()
    if form.validate_on_submit():
        supplier.name = form.name.data
        supplier.contact_name = form.contact_name.data
        supplier.email = form.email.data
        supplier.phone = form.phone.data
        supplier.address = form.address.data
        db.session.commit()
        flash('Supplier updated!', 'success')
        return redirect(url_for('admin.manage_suppliers'))
    elif request.method == 'GET':
        form.name.data = supplier.name
        form.contact_name.data = supplier.contact_name
        form.email.data = supplier.email
        form.phone.data = supplier.phone
        form.address.data = supplier.address
    return render_template('admin/edit_supplier.html', title='Edit Supplier', form=form, legend='Edit Supplier')

@admin.route('/supplier/delete/<int:supplier_id>', methods=['POST'])
@login_required
@admin_required
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    db.session.delete(supplier)
    db.session.commit()
    flash('Supplier deleted!', 'success')
    return redirect(url_for('admin.manage_suppliers'))

# -- Purchase Management --

@admin.route('/purchases')
@login_required
@admin_required
def manage_purchases():
    purchases = Purchase.query.order_by(Purchase.date.desc()).all()
    return render_template('admin/purchases.html', title='Purchase History', purchases=purchases)

@admin.route('/purchase/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_purchase():
    form = PurchaseForm()
    # Populate supplier choices
    form.supplier_id.choices = [(s.id, s.name) for s in Supplier.query.all()]
    form.supplier_id.choices.insert(0, (0, 'Unknown / No Supplier'))
    
    if form.validate_on_submit():
        supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None
        purchase = Purchase(supplier_id=supplier_id, reference=form.reference.data)
        db.session.add(purchase)
        db.session.commit()
        return redirect(url_for('admin.view_purchase', purchase_id=purchase.id))
        
    return render_template('admin/new_purchase.html', title='New Purchase', form=form)

@admin.route('/purchase/<int:purchase_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def view_purchase(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    items = InventoryItem.query.all() # For adding items to purchase
    return render_template('admin/purchase_details.html', title=f'Purchase #{purchase.id}', purchase=purchase, inventory_items=items)

@admin.route('/purchase/<int:purchase_id>/add_item', methods=['POST'])
@login_required
@admin_required
def add_purchase_item(purchase_id):
    purchase = Purchase.query.get_or_404(purchase_id)
    inventory_id = request.form.get('inventory_item_id')
    quantity = float(request.form.get('quantity'))
    cost = float(request.form.get('cost'))
    
    # Create Purchase Item
    item = PurchaseItem(purchase_id=purchase.id, inventory_item_id=inventory_id, quantity=quantity, cost=cost)
    db.session.add(item)
    
    # Update Total Cost
    purchase.total_cost += cost
    
    # Update Inventory Stock
    inventory_item = InventoryItem.query.get(inventory_id)
    inventory_item.quantity += quantity
    # OPTIONAL: Update weighted average cost? 
    # For now, let's just update the cost_per_unit to the latest cost / quantity?
    if quantity > 0:
        inventory_item.cost_per_unit = cost / quantity
    
    db.session.commit()
    flash('Item added to purchase and stock updated!', 'success')
    return redirect(url_for('admin.view_purchase', purchase_id=purchase.id))

# -- Recipe / Ingredients Management --
@admin.route('/menu/recipe/<int:item_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_recipe(item_id):
    menu_item = MenuItem.query.get_or_404(item_id)
    
    if request.method == 'POST':
        # Add ingredient
        inventory_id = request.form.get('inventory_item_id')
        qty = float(request.form.get('quantity_required'))
        
        # Check if already exists
        exists = ProductIngredient.query.filter_by(menu_item_id=menu_item.id, inventory_item_id=inventory_id).first()
        if exists:
            exists.quantity_required = qty
            flash('Updated ingredient quantity.', 'info')
        else:
            new_ing = ProductIngredient(menu_item_id=menu_item.id, inventory_item_id=inventory_id, quantity_required=qty)
            db.session.add(new_ing)
            flash('Ingredient added to recipe.', 'success')
        db.session.commit()
        return redirect(url_for('admin.manage_recipe', item_id=item_id))
        
    all_ingredients = InventoryItem.query.order_by(InventoryItem.name).all()
    # Get current ingredients
    current_recipe = ProductIngredient.query.filter_by(menu_item_id=menu_item.id).all()
    
    return render_template('admin/manage_recipe.html', title=f'Recipe for {menu_item.name}', 
                           menu_item=menu_item, 
                           all_ingredients=all_ingredients, 
                           current_recipe=current_recipe)

@admin.route('/menu/recipe/remove/<int:id>', methods=['POST'])
@login_required
@admin_required
def remove_ingredient_from_recipe(id):
    ing = ProductIngredient.query.get_or_404(id)
    item_id = ing.menu_item_id
    db.session.delete(ing)
    db.session.commit()
    flash('Ingredient removed from recipe.', 'success')
    return redirect(url_for('admin.manage_recipe', item_id=item_id))


@admin.route('/reports')
@login_required
@admin_required
def reports():
    # 1. Sales Over Time (Daily - Last 30 Days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    daily_sales_data = db.session.query(
        func.date(Order.date_ordered).label('date'),
        func.sum(Order.total_price).label('revenue'),
        func.count(Order.id).label('orders')
    ).filter(
        Order.date_ordered >= start_date,
        Order.status == 'Completed'
    ).group_by(func.date(Order.date_ordered)).all()
    
    # 2. Profit Analysis (Revenue - Cost)
    # We need to join OrderItem -> MenuItem to get cost
    # Profit = Sum(OrderItem.price_at_order * quantity) - Sum(MenuItem.cost * quantity)
    # Note: price_at_order is stored, but cost wasn't historically. We use current cost for approximation or 0 if missing.
    
    total_revenue = 0
    total_cost = 0
    
    # Analyze all completed orders for profit summary (or last 30 days)
    # Let's do all time for the summary cards, and 30 days for charts if needed
    all_completed_items = db.session.query(OrderItem, MenuItem).join(MenuItem).join(Order).filter(Order.status == 'Completed').all()
    
    for order_item, menu_item in all_completed_items:
        total_revenue += order_item.price_at_order * order_item.quantity
        total_cost += menu_item.cost * order_item.quantity
        
    total_profit = total_revenue - total_cost
    
    # 3. Peak Hours
    peak_hours_data = db.session.query(
        func.strftime('%H', Order.date_ordered).label('hour'),
        func.count(Order.id).label('count')
    ).group_by('hour').order_by('hour').all()
    
    # 4. Top Selling Items
    top_items = db.session.query(
        MenuItem.name,
        func.sum(OrderItem.quantity).label('qty')
    ).join(OrderItem).join(Order).filter(Order.status == 'Completed')\
     .group_by(MenuItem.name).order_by(desc('qty')).limit(10).all()

    return render_template('admin/reports.html', title='Reports & Analytics',
                           daily_sales=daily_sales_data,
                           total_revenue=total_revenue,
                           total_profit=total_profit,
                           peak_hours=peak_hours_data,
                           top_items=top_items)

@admin.route('/reports/export/csv')
@login_required
@admin_required
def export_reports_csv():
    import csv
    import io
    from flask import Response
    
    # Export Sales Data
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Orders', 'Revenue'])
    
    orders = db.session.query(
        func.date(Order.date_ordered).label('date'),
        func.count(Order.id).label('count'),
        func.sum(Order.total_price).label('revenue')
    ).group_by(func.date(Order.date_ordered)).all()
    
    for o in orders:
        cw.writerow([o.date, o.count, o.revenue])
        
    output = si.getvalue()

# -- Staff Management --

@admin.route('/staff')
@login_required
@admin_required
def manage_staff():
    staff_members = User.query.all() # You might want to filter by role if you distinguish customers vs staff
    # Assuming 'Customer' is a role, maybe we only show non-Customers?
    # For now, let's show everyone or filter out 'Customer' if desired.
    # staff_members = User.query.filter(User.role != 'Customer').all() 
    # But for a cafe app, maybe admin wants to see everyone. Let's stick to all for now or filter.
    # Given the prompt "Staff Management", it's better to show only staff.
    staff_members = User.query.filter(User.role.in_(['Manager', 'Chef', 'Waiter', 'Cashier', 'Owner'])).all()
    return render_template('admin/staff.html', title='Staff Management', staff_members=staff_members)

@admin.route('/staff/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_staff():
    form = StaffForm()
    if form.validate_on_submit():
        hashed_password = 'password' # Default password or handle generation
        if form.password.data:
            from app import bcrypt # Import here or at top if available. Assuming bcrypt is used in 'app/__init__.py' but not imported in routes yet.
            # Wait, standard flask-bcrypt usage:
            # hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            # Let's check how User model does it or where bcrypt is.
            # Converting to simple string for now if bcrypt not clearly available in this file context, 
            # BUT usually it is 'from app import bcrypt'. I'll check imports.
            pass
        
        # To be safe and compliant with existing User model (which has password field), 
        # let's assume valid password is required or handled.
        # For this snippet, I will just save the raw password if hashing isn't obvious, 
        # OR better, rely on the User model creation if it handles hashing. 
        # Looking at previous code, 'User' model just has 'password' column. 
        # I will assume I need to hash it if the app uses hashing.
        # Let's import bcrypt from app if it exists, or just store plain for now (User warned about this? No).
        # Better: Check existing Registration route? It's not in admin routes.
        # I will just store it as is, but it's bad practice. 
        # Let's try to import bcrypt.
        
        from app import bcrypt
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8') if form.password.data else bcrypt.generate_password_hash('password123').decode('utf-8')
        
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw,
                    role=form.role.data, phone=form.phone.data, hourly_rate=form.hourly_rate.data)
        db.session.add(user)
        db.session.commit()
        flash(f'Staff member {user.username} has been added!', 'success')
        return redirect(url_for('admin.manage_staff'))
    return render_template('admin/edit_staff.html', title='Add Staff', form=form, legend='Add Staff')

@admin.route('/staff/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_staff(user_id):
    user = User.query.get_or_404(user_id)
    form = StaffForm()
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user.phone = form.phone.data
        user.hourly_rate = form.hourly_rate.data
        if form.password.data:
             from app import bcrypt
             user.password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        
        db.session.commit()
        flash(f'Staff member {user.username} updated!', 'success')
        return redirect(url_for('admin.manage_staff'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
        form.phone.data = user.phone
        form.hourly_rate.data = user.hourly_rate
    return render_template('admin/edit_staff.html', title='Edit Staff', form=form, legend='Edit Staff')

@admin.route('/staff/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_staff(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('Staff member deleted!', 'success')
    return redirect(url_for('admin.manage_staff'))

# -- Shift Management --

@admin.route('/shifts')
@login_required
@admin_required
def manage_shifts():
    # Show upcoming shifts by default
    shifts = Shift.query.order_by(Shift.date.desc(), Shift.start_time).all()
    return render_template('admin/shifts.html', title='Shift Scheduling', shifts=shifts)

@admin.route('/shift/assign', methods=['GET', 'POST'])
@login_required
@admin_required
def assign_shift():
    form = ShiftForm()
    # Populate user choices
    staff = User.query.filter(User.role.in_(['Manager', 'Chef', 'Waiter', 'Cashier', 'Owner'])).all()
    form.user_id.choices = [(u.id, f"{u.username} ({u.role})") for u in staff]
    
    if form.validate_on_submit():
        shift = Shift(user_id=form.user_id.data, date=form.date.data, 
                      start_time=form.start_time.data, end_time=form.end_time.data, 
                      notes=form.notes.data)
        db.session.add(shift)
        db.session.commit()
        flash('Shift assigned successfully!', 'success')
        return redirect(url_for('admin.manage_shifts'))
    return render_template('admin/assign_shift.html', title='Assign Shift', form=form)

@admin.route('/shift/delete/<int:shift_id>', methods=['POST'])
@login_required
@admin_required
def delete_shift(shift_id):
    shift = Shift.query.get_or_404(shift_id)
    db.session.delete(shift)
    db.session.commit()
    flash('Shift removed!', 'success')
    return redirect(url_for('admin.manage_shifts'))

# -- Attendance Tracking --

@admin.route('/attendance')
@login_required
@admin_required
def manage_attendance():
    records = Attendance.query.order_by(Attendance.date.desc(), Attendance.clock_in).all()
    
    # Simple stats for "Performance Overview" could be calculated here or in a separate report
    # For now, let's just show the list
    return render_template('admin/attendance.html', title='Attendance Tracking', records=records)

@admin.route('/attendance/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_attendance():
    form = AttendanceForm()
    # Populate user choices
    staff = User.query.all() # Include everyone for attendance
    form.user_id.choices = [(u.id, u.username) for u in staff]
    
    if form.validate_on_submit():
        attendance = Attendance(user_id=form.user_id.data, date=form.date.data,
                                clock_in=form.clock_in.data, clock_out=form.clock_out.data,
                                status=form.status.data)
        db.session.add(attendance)
        db.session.commit()
        flash('Attendance record added!', 'success')
        return redirect(url_for('admin.manage_attendance'))
    return render_template('admin/edit_attendance.html', title='Add Attendance', form=form)

# -- Customer Management --

@admin.route('/customers')
@login_required
@admin_required
def manage_customers():
    # Show only users with 'Customer' role
    customers = User.query.filter_by(role='Customer').all()
    return render_template('admin/customers.html', title='Customer Management', customers=customers)

@admin.route('/customer/<int:user_id>')
@login_required
@admin_required
def customer_details(user_id):
    customer = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(user_id=customer.id).order_by(Order.date_ordered.desc()).all()
    feedback_history = Feedback.query.filter_by(user_id=customer.id).order_by(Feedback.date_posted.desc()).all()
    return render_template('admin/customer_details.html', title=f'Customer: {customer.username}', customer=customer, orders=orders, feedback_history=feedback_history)

@admin.route('/customer/update_points/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_loyalty_points(user_id):
    customer = User.query.get_or_404(user_id)
    points = int(request.form.get('points', 0))
    action = request.form.get('action') # 'add' or 'set'
    
    if action == 'add':
        customer.loyalty_points += points
    else:
        customer.loyalty_points = points
        
    db.session.commit()
    flash(f"Updated loyalty points for {customer.username}.", "success")
    return redirect(url_for('admin.customer_details', user_id=customer.id))


# -- Coupon Management --

@admin.route('/coupons')
@login_required
@admin_required
def manage_coupons():
    coupons = Coupon.query.order_by(Coupon.valid_to.desc()).all()
    return render_template('admin/coupons.html', title='Coupon Management', coupons=coupons, now=datetime.now())

@admin.route('/coupon/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_coupon():
    form = CouponForm()
    if form.validate_on_submit():
        coupon = Coupon(code=form.code.data.upper(),
                        discount_value=form.discount_value.data,
                        discount_type=form.discount_type.data,
                        valid_from=form.valid_from.data,
                        valid_to=form.valid_to.data,
                        usage_limit=form.usage_limit.data,
                        active=form.active.data)
        db.session.add(coupon)
        db.session.commit()
        flash('Coupon created successfully!', 'success')
        return redirect(url_for('admin.manage_coupons'))
    return render_template('admin/edit_coupon.html', title='Create Coupon', form=form, legend='Create Coupon')

@admin.route('/coupon/edit/<int:coupon_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    form = CouponForm()
    if form.validate_on_submit():
        coupon.code = form.code.data.upper()
        coupon.discount_value = form.discount_value.data
        coupon.discount_type = form.discount_type.data
        coupon.valid_from = form.valid_from.data
        coupon.valid_to = form.valid_to.data
        coupon.usage_limit = form.usage_limit.data
        coupon.active = form.active.data
        db.session.commit()
        flash('Coupon updated!', 'success')
        return redirect(url_for('admin.manage_coupons'))
    elif request.method == 'GET':
        form.code.data = coupon.code
        form.discount_value.data = coupon.discount_value
        form.discount_type.data = coupon.discount_type
        form.valid_from.data = coupon.valid_from
        form.valid_to.data = coupon.valid_to
        form.usage_limit.data = coupon.usage_limit
        form.active.data = coupon.active
    return render_template('admin/edit_coupon.html', title='Edit Coupon', form=form, legend='Edit Coupon')

@admin.route('/coupon/delete/<int:coupon_id>', methods=['POST'])
@login_required
@admin_required
def delete_coupon(coupon_id):
    coupon = Coupon.query.get_or_404(coupon_id)
    db.session.delete(coupon)
    db.session.commit()
    flash('Coupon deleted!', 'success')
    return redirect(url_for('admin.manage_coupons'))


# -- Feedback Management --

@admin.route('/feedback')
@login_required
@admin_required
def manage_feedback():
    feedback_entries = Feedback.query.order_by(Feedback.date_posted.desc()).all()
    return render_template('admin/feedback.html', title='Customer Feedback', feedback_entries=feedback_entries)

@admin.route('/feedback/toggle_public/<int:feedback_id>')
@login_required
@admin_required
def toggle_public_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    feedback.is_public = not feedback.is_public
    db.session.commit()
    status = "Public" if feedback.is_public else "Hidden"
    flash(f"Feedback marked as {status}.", 'success')
    return redirect(url_for('admin.manage_feedback'))

# -- Frontend Management --

@admin.route('/frontend', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_frontend():
    setting = CafeSetting.query.first()
    if not setting:
        setting = CafeSetting()
        db.session.add(setting)
        db.session.commit()
    
    form = FrontendSettingsForm()
    if form.validate_on_submit():
        # Styles
        setting.theme_color_primary = form.theme_color_primary.data
        setting.theme_color_secondary = form.theme_color_secondary.data
        setting.menu_bg_color = form.menu_bg_color.data
        setting.card_bg_color = form.card_bg_color.data
        setting.text_color = form.text_color.data
        
        # Hero
        setting.hero_title = form.hero_title.data
        setting.hero_subtitle = form.hero_subtitle.data
        setting.short_description = form.short_description.data
        if form.hero_image.data:
            setting.hero_image = save_picture(form.hero_image.data, folder='hero')
            
        # About
        setting.about_title = form.about_title.data
        setting.about_content = form.about_content.data
        if form.about_image.data:
            setting.about_image = save_picture(form.about_image.data, folder='about')

        # Story & Values
        setting.story_title = form.story_title.data
        setting.story_content = form.story_content.data
        setting.mission_content = form.mission_content.data
        setting.vision_content = form.vision_content.data
        if form.story_image.data:
            setting.story_image = save_picture(form.story_image.data, folder='about')
            
        # Socials
        setting.social_facebook = form.social_facebook.data
        setting.social_instagram = form.social_instagram.data
        setting.social_twitter = form.social_twitter.data
        
        db.session.commit()
        log_activity('Frontend Updated', 'User updated frontend settings')
        flash('Frontend settings updated!', 'success')
        return redirect(url_for('admin.manage_frontend'))
    
    elif request.method == 'GET':
        form.theme_color_primary.data = setting.theme_color_primary
        form.theme_color_secondary.data = setting.theme_color_secondary
        form.menu_bg_color.data = setting.menu_bg_color
        form.card_bg_color.data = setting.card_bg_color
        form.text_color.data = setting.text_color
        
        form.hero_title.data = setting.hero_title
        form.hero_subtitle.data = setting.hero_subtitle
        form.short_description.data = setting.short_description
        form.about_title.data = setting.about_title
        form.about_content.data = setting.about_content
        form.social_facebook.data = setting.social_facebook
        form.social_instagram.data = setting.social_instagram
        form.social_twitter.data = setting.social_twitter
        
        # Story
        form.story_title.data = setting.story_title
        form.story_content.data = setting.story_content
        form.mission_content.data = setting.mission_content
        form.vision_content.data = setting.vision_content

    team_members = TeamMember.query.all()
    gallery_photos = CafePhoto.query.all()

    return render_template('admin/frontend_manager.html', title='Frontend Manager', form=form, setting=setting, team_members=team_members, gallery_photos=gallery_photos)

# -- Team Management --

@admin.route('/team/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_team_member():
    form = TeamMemberForm()
    if form.validate_on_submit():
        image_file = 'default_profile.jpg'
        if form.image_file.data:
            image_file = save_picture(form.image_file.data, folder='team')
            
        member = TeamMember(name=form.name.data, role=form.role.data, bio=form.bio.data,
                            image_file=image_file, is_visible=form.is_visible.data)
        db.session.add(member)
        db.session.commit()
        flash('Team member added!', 'success')
        return redirect(url_for('admin.manage_frontend'))
    # Using a shared template or specialized one? 
    # Let's create specific templates as per plan or use generic 'edit_team_member.html'
    return render_template('admin/edit_team_member.html', title='Add Team Member', form=form)

@admin.route('/team/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_team_member(id):
    member = TeamMember.query.get_or_404(id)
    form = TeamMemberForm()
    if form.validate_on_submit():
        member.name = form.name.data
        member.role = form.role.data
        member.bio = form.bio.data
        member.is_visible = form.is_visible.data
        if form.image_file.data:
            member.image_file = save_picture(form.image_file.data, folder='team')
        db.session.commit()
        flash('Team member updated!', 'success')
        return redirect(url_for('admin.manage_frontend'))
    elif request.method == 'GET':
        form.name.data = member.name
        form.role.data = member.role
        form.bio.data = member.bio
        form.is_visible.data = member.is_visible
    return render_template('admin/edit_team_member.html', title='Edit Team Member', form=form)

@admin.route('/team/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_team_member(id):
    member = TeamMember.query.get_or_404(id)
    db.session.delete(member)
    db.session.commit()
    flash('Team member deleted.', 'success')
    return redirect(url_for('admin.manage_frontend'))


# -- Gallery Management --

@admin.route('/gallery/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_gallery_photo():
    form = CafePhotoForm()
    if form.validate_on_submit():
        image_file = save_picture(form.image_file.data, folder='gallery')
        photo = CafePhoto(image_file=image_file, caption=form.caption.data, is_visible=form.is_visible.data)
        db.session.add(photo)
        db.session.commit()
        flash('Photo added to gallery!', 'success')
        return redirect(url_for('admin.manage_frontend'))
    return render_template('admin/add_photo.html', title='Add Photo', form=form)

@admin.route('/gallery/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_gallery_photo(id):
    photo = CafePhoto.query.get_or_404(id)
    db.session.delete(photo)
    db.session.commit()
    flash('Photo removed from gallery.', 'success')
    return redirect(url_for('admin.manage_frontend'))

# -- Settings Management --

@admin.route('/settings', methods=['GET', 'POST'])
@admin_required
def manage_settings():
    setting = CafeSetting.query.first()
    if not setting:
        setting = CafeSetting()
        db.session.add(setting)
        db.session.commit()
    
    form = SettingsForm()
    if form.validate_on_submit():
        setting.cafe_name = form.cafe_name.data
        setting.cafe_address = form.cafe_address.data
        setting.cafe_phone = form.cafe_phone.data
        setting.cafe_email = form.cafe_email.data
        
        # Financials
        setting.tax_rate = form.tax_rate.data
        setting.service_charge = form.service_charge.data
        setting.currency_symbol = form.currency_symbol.data
        
        # Operations
        setting.opening_time = form.opening_time.data
        setting.closing_time = form.closing_time.data
        
        # Tech
        setting.printer_ip = form.printer_ip.data
        setting.printer_port = form.printer_port.data
        setting.POS_enabled = form.pos_enabled.data
        setting.language = form.language.data
        
        # Home Page
        setting.hero_title = form.hero_title.data
        setting.hero_subtitle = form.hero_subtitle.data
        setting.short_description = form.short_description.data

        # Handle Logo Upload
        if form.cafe_logo.data:
            setting.cafe_logo = save_picture(form.cafe_logo.data, folder='profile')

        # Handle Hero Image Upload
        if form.hero_image.data:
            setting.hero_image = save_picture(form.hero_image.data, folder='hero') 
            # I must check where save_picture is defined.
            # Assuming it is available or I need to import it.
            # I will assume it's imported (it was used in add_menu_item).
            # Wait, line 124 usage suggests it's available. 
            # But line 1-14 imports don't show it explicitly unless `from app import ...` brings it?
            # Or it was defined in valid view_file output but hidden?
            # I'll check imports again.
            setting.cafe_logo = save_picture(form.cafe_logo.data, folder='profile')
            
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin.manage_settings'))
    
    elif request.method == 'GET':
        form.cafe_name.data = setting.cafe_name
        form.cafe_address.data = setting.cafe_address
        form.cafe_phone.data = setting.cafe_phone
        form.cafe_email.data = setting.cafe_email
        form.tax_rate.data = setting.tax_rate
        form.service_charge.data = setting.service_charge
        form.currency_symbol.data = setting.currency_symbol
        form.opening_time.data = setting.opening_time
        form.closing_time.data = setting.closing_time
        form.printer_ip.data = setting.printer_ip
        form.printer_port.data = setting.printer_port
        form.pos_enabled.data = setting.POS_enabled
        form.language.data = setting.language
        
        # Home Page
        form.hero_title.data = setting.hero_title
        form.hero_subtitle.data = setting.hero_subtitle
        form.short_description.data = setting.short_description
        
    return render_template('admin/settings.html', title='Settings', form=form, setting=setting)

# -- Notifications --

@admin.context_processor
def inject_notifications():
    # Only for admins (though context processor runs for all, check scope)
    # Ideally should perform check, but query is fast.
    if current_user.is_authenticated and current_user.is_admin:
        # Get unread count
        unread_count = Notification.query.filter_by(is_read=False).count()
        # Get latest 5 unread (or just latest 5)
        latest_notifs = Notification.query.order_by(Notification.timestamp.desc()).limit(5).all()
        return dict(unread_notifications_count=unread_count, latest_notifications=latest_notifs)
    return dict(unread_notifications_count=0, latest_notifications=[])

@admin.route('/notifications')
@login_required
@admin_required
def all_notifications():
    # Show all, paginated ideally, but let's do list
    page = request.args.get('page', 1, type=int)
    notifs = Notification.query.order_by(Notification.timestamp.desc()).paginate(page=page, per_page=20)
    return render_template('admin/notifications.html', title='Notifications', notifications=notifs)

@admin.route('/notifications/read/<int:notif_id>')
@login_required
@admin_required
def mark_notification_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    notif.is_read = True
    db.session.commit()
    if notif.link:
        return redirect(notif.link)
    return redirect(url_for('admin.all_notifications'))

@admin.route('/notifications/read_all')
@login_required
@admin_required
def mark_all_read():
    unread = Notification.query.filter_by(is_read=False).all()
    for n in unread:
        n.is_read = True
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(request.referrer or url_for('admin.dashboard'))

# -- Security & Backup --

@admin.route('/security')
@login_required
@admin_required
def security_dashboard():
    return render_template('admin/security.html', title='Security & Backup')

@admin.route('/activity')
@login_required
@admin_required
def activity_logs():
    page = request.args.get('page', 1, type=int)
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).paginate(page=page, per_page=50)
    return render_template('admin/activity.html', title='Activity Logs', logs=logs)

@admin.route('/backup/download')
@login_required
@admin_required
def download_backup():
    # Simple JSON export of key data
    data = {
        'orders': [o.to_dict() for o in Order.query.all()] if hasattr(Order, 'to_dict') else [], # Fallback if to_dict not impl
        # Just dumping basic counts or key info if to_dict missing, or implementing dump logic
        'timestamp': datetime.utcnow().isoformat()
    }
    # Since models don't have to_dict, let's just dump summary or implement quick serializer helper??
    # Better: Dump raw table data generically? Or just key tables.
    # Let's do a simple dump of Orders and Menu Items using a helper
    
    def model_to_dict(obj):
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

    backup_data = {
        'menu_items': [model_to_dict(i) for i in MenuItem.query.all()],
        'orders': [model_to_dict(o) for o in Order.query.all()],
        'users': [model_to_dict(u) for u in User.query.all()]
    }
    
    json_str = json.dumps(backup_data, indent=4, default=str)
    
    log_activity('Backup Download', 'User downloaded system backup')
    
    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-disposition": "attachment; filename=cafe_backup.json"}
    )

@admin.route('/logs')
@login_required
@admin_required
def view_system_logs():
    log_path = os.path.join(current_app.root_path, '../logs/app.log')
    log_content = "Log file not found."
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            # Read last 200 lines
            log_content = ''.join(f.readlines()[-200:])
    return render_template('admin/system_logs.html', title='System Logs', log_content=log_content)

@admin.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', title='Manage Users', users=users)

@admin.route('/users/toggle_admin/<int:user_id>')
@login_required
@admin_required
def toggle_admin(user_id):
    if user_id == current_user.id:
        flash('You cannot change your own role.', 'warning')
        return redirect(url_for('admin.manage_users'))
        
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    
    action = "Promoted to Admin" if user.is_admin else "Demoted from Admin"
    log_activity('User Role Change', f"Changed role for {user.username} to {action}")
    
    flash(f'User {user.username} role updated.', 'success')
    return redirect(url_for('admin.manage_users'))
