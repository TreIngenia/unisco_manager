from flask import Blueprint

web_bp = Blueprint('web', __name__)

from app.routes.web import register_web_routes
register_web_routes(web_bp)