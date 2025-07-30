from flask import Flask, g, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from app.config import config
import os
import click
from app.error_handlers import register_error_handlers
from app.cli.commands import register_cli_commands


# Inizializzazione estensioni
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name=None):
    app = Flask(__name__)
    register_cli_commands(app)
    
    # Configurazione
    config_name = config_name or os.environ.get('FLASK_CONFIG', 'default')
    app.config.from_object(config[config_name])
    
    # Inizializzazione estensioni
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    
    # Registrazione blueprints
    from app.auth import auth_bp
    from app.web import web_bp
    from app.api import api_bp
    from app.admin import admin_bp
    from app.voip_cdr import admin_voip_cdr
    from app.voip_cdr import api_voip_cdr
    from app.voip_cdr import api_odoo

    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(admin_voip_cdr)
    app.register_blueprint(api_voip_cdr)
    app.register_blueprint(api_odoo)

    #reindirizza le pagine di errore
    # register_error_handlers(app)
    
    # Importazione modelli per le migrazioni
    from app.models import User, Role, Company
    
    # Registrazione context processor per templates
    @app.context_processor
    def inject_user():
        return dict(current_user=g.get('user'))
    
    # Registrazione funzioni menu per templates
    @app.context_processor
    def inject_menu():
        from app.utils.menu import get_menu, get_menu_stats,get_breadcrumb
        return dict(
            get_menu=get_menu,
            menu_stats=get_menu_stats,
            get_breadcrumb=get_breadcrumb
        )
    
    @app.context_processor
    def inject_menu():
        from app.utils.custom_menu import get_predefined_menu, get_custom_menu, get_children_menu
        return dict(
            get_predefined_menu=get_predefined_menu,
            get_custom_menu=get_custom_menu,
            get_children_menu=get_children_menu
        )
    
    @app.context_processor
    def inject_datetime():
        from datetime import datetime
        return dict(
            now=datetime.now,
            datetime=datetime,
            utcnow=datetime.utcnow,         #Modificato
            current_time=datetime.now()     #Modificato
        )
    
    # Middleware per caricare utente da sessione
    @app.before_request
    def load_user():
        from app.auth.jwt_session import load_unified_user
        load_unified_user()
    
    # Blocca la cache delle pagine html
    @app.after_request
    def add_security_headers(response):
        """Aggiunge header di sicurezza per prevenire cache su pagine protette"""
        # Controlla se la richiesta è per una pagina protetta
        if request.endpoint and not request.endpoint.startswith('auth.'):
            # Impedisce cache del browser
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response
    
    # @app.before_request
    # def load_user():
    #     from app.auth.jwt_session import unified_login_required
    #     from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
    #     # Prima prova JWT cookie
    #     try:
    #         verify_jwt_in_request(optional=True)
    #         user_uid = get_jwt_identity()
    #         if user_uid:
    #             user = User.query.get(user_uid)
    #             if user and user.is_active:
    #                 g.user = user
    #                 return
    #     except Exception:
    #         pass
        
    #     # Fallback su sessione esistente
    #     user_uid = session.get('user_uid')
    #     if user_uid:
    #         user = User.query.get(user_uid)
    #         if user and user.is_active and not user.is_active:
    #             g.user = None
    #             session.clear()
    #         else:
    #             g.user = user
    #     else:
    #         g.user = None


    
    
    return app