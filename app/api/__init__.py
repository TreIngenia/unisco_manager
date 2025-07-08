from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from app.routes.api import register_api_routes
register_api_routes(api_bp)