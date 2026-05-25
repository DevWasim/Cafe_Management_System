from flask import render_template, jsonify, request, flash, redirect, url_for
from app import db
from app.admin import admin
from app.models import Reservation, Table
from app.admin.routes import admin_required
from datetime import datetime

@admin.route('/reservations')
@admin_required
def manage_reservations():
    # Fetch upcoming reservations
    upcoming = Reservation.query.filter(Reservation.date >= datetime.utcnow().date()).order_by(Reservation.date.asc(), Reservation.time.asc()).all()
    return render_template('admin/reservations/index.html', title='Manage Reservations', reservations=upcoming)

@admin.route('/api/reservations/calendar')
@admin_required
def get_calendar_events():
    start = request.args.get('start')
    end = request.args.get('end')
    
    # In real app filter by date range
    reservations = Reservation.query.all()
    
    events = []
    for res in reservations:
        # Construct ISO datetime manually for FullCalendar
        start_dt = f"{res.date}T{res.time}"
        
        # Assume 1.5 hours duration
        end_dt = datetime.combine(res.date, res.time) + __import__('datetime').timedelta(hours=1, minutes=30)
        end_dt_str = end_dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        color = '#3788d8' # Blue default
        if res.status == 'Confirmed': color = '#28a745'
        if res.status == 'Cancelled': color = '#dc3545'
        if res.status == 'Pending': color = '#ffc107'

        events.append({
            'title': f"{res.name} ({res.party_size}p)",
            'start': start_dt,
            'end': end_dt_str,
            'color': color,
            'url': '#' # Could link to detail modal
        })
        
    return jsonify(events)
