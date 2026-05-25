from flask import render_template, jsonify, request
from app import db
from app.admin import admin
from app.models import Order, OrderItem
from app.admin.routes import admin_required
from datetime import datetime, timedelta

@admin.route('/kitchen')
@admin_required
def kds_index():
    return render_template('admin/kds/index.html', title='Kitchen Display')

@admin.route('/api/kds/orders')
@admin_required
def kds_get_orders():
    # Fetch orders that are pending or preparing
    # We ignore 'Completed' or 'Cancelled'
    active_statuses = ['Pending', 'Preparing']
    
    orders = Order.query.filter(Order.status.in_(active_statuses)).order_by(Order.date_ordered.asc()).all()
    
    orders_data = []
    for order in orders:
        items = []
        for item in order.items:
            # Format options string if exists
            options_text = ""
            special_notes = ""
            
            if item.options:
                opts = []
                for k, v in item.options.items():
                    if k == 'notes':
                        special_notes = v
                        continue
                        
                    if isinstance(v, list):
                        v = ", ".join(v)
                    opts.append(f"{k}: {v}")
                options_text = " | ".join(opts)

            items.append({
                'name': item.item.name,
                'quantity': item.quantity,
                'options': options_text,
                'notes': special_notes,
                'category': item.item.category
            })
            
        # Calculate time pending
        # Return naive datetime string for JS to parse and count up
        # Ensure it has 'Z' if it's naive UTC
        time_ordered_iso = order.date_ordered.isoformat()
        if not order.date_ordered.tzinfo:
             time_ordered_iso += 'Z'
        
        orders_data.append({
            'id': order.id,
            'table': order.table_number if order.table_number else 'Takeaway',
            'type': order.order_type,
            'status': order.status, # 'Pending' or 'Preparing'
            'time_ordered_iso': time_ordered_iso, 
            'items': items
        })
        
    return jsonify(orders_data)

@admin.route('/api/kds/update_status/<int:order_id>/<string:new_status>', methods=['POST'])
@admin_required
def kds_update_status(order_id, new_status):
    order = Order.query.get_or_404(order_id)
    
    # Valid transitions logic could go here
    if new_status in ['Ready', 'Completed', 'Preparing']:
        order.status = new_status
        db.session.commit()
        return jsonify({'success': True})
        
    return jsonify({'success': False, 'message': 'Invalid Status'}), 400
