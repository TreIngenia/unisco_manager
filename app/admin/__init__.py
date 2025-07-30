from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
from app.routes.admin import register_admin_routes
register_admin_routes(admin_bp)