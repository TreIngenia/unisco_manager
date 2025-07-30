from flask import Blueprint

admin_voip_cdr = Blueprint('admin_voip_cdr', __name__, url_prefix='/admin')
from app.routes.voip_cdr import register_voip_cdr_routes, create_listino_routes
register_voip_cdr_routes(admin_voip_cdr)
create_listino_routes(admin_voip_cdr)


api_voip_cdr = Blueprint('api_voip_cdr', __name__, url_prefix='/api')
from app.routes.api_voip_cdr import register_api_voip_cdr_routes
register_api_voip_cdr_routes(api_voip_cdr)

api_odoo = Blueprint('api_odoo', __name__, url_prefix='/api')
from app.routes.odoo import register_api_odoo_routes
register_api_odoo_routes(api_odoo)