from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

from app.routes.auth import register_auth_routes
register_auth_routes(auth_bp)