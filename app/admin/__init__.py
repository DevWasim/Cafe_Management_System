from flask import Blueprint

admin = Blueprint('admin', __name__)

from app.admin import routes, pos_routes, kds_routes, reservations_routes
