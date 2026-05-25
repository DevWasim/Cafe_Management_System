from flask import render_template, jsonify, request, flash, redirect, url_for
from app import db
from app.admin import admin
from app.models import MenuItem, Order, OrderItem, User, CafeSetting
from app.admin.routes import admin_required
from flask_login import current_user
import json
from datetime import datetime

@admin.route('/pos')
@admin_required
def pos_index():
    # Get all categories for tabs
    categories = db.session.query(MenuItem.category).distinct().all()
    categories = [c[0] for c in categories]
    
    # Get all items grouped or just all items to be filtered by JS
    items = MenuItem.query.filter_by(is_available=True).all()
    
    return render_template('admin/pos/index.html', title='POS', categories=categories, items=items)

@admin.route('/api/pos/products')
@admin_required
def pos_get_products():
    items = MenuItem.query.filter_by(is_available=True).all()
    products = []
    for item in items:
        products.append({
            'id': item.id,
            'name': item.name,
            'price': item.price,
            'category': item.category,
            'image': item.image_file,
            'options': item.options
        })
    return jsonify(products)

@admin.route('/api/pos/create_order', methods=['POST'])
@admin_required
def pos_create_order():
    data = request.get_json()
    
    if not data or 'cart' not in data:
        return jsonify({'success': False, 'message': 'Empty cart'}), 400
        
    try:
        # Create Order
        total_price = data.get('total', 0)
        payment_method = data.get('payment_method', 'Cash')
        
        # Determine Status based on payment
        # POS orders are usually "Completed" immediately if cash/card, or "Preparing" if Kitchen needs to see it
        # Let's say "Preparing" so KDS can see it, but Payment Status is "Paid"
        
        new_order = Order(
            user_id=current_user.id, # Staff member who took the order
            total_price=total_price,
            status='Preparing',
            order_type='POS',
            payment_method=payment_method,
            payment_status='Paid',
            table_number=data.get('table_number', 0)
        )
        
        db.session.add(new_order)
        db.session.commit()
        
        # Add Items
        for item in data['cart']:
            order_item = OrderItem(
                order_id=new_order.id,
                menu_item_id=item['id'],
                quantity=item['quantity'],
                price_at_order=item['price'],
                options=item.get('options', {}) # Save selected modifiers
            )
            db.session.add(order_item)
            
            # TODO: Inventory deduction here (reusing logic or signal)
            
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'order_id': new_order.id, 
            'message': f'Order #{new_order.id} Created'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
