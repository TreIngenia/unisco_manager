from flask import Flask, g, session, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from app.config import config
import os
import click
from app.error_handlers import register_error_handlers

# Inizializzazione estensioni
db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()

def create_app(config_name=None):
    app = Flask(__name__)
    
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
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    
    #reindirizza le pagine di errore
    # register_error_handlers(app)
    
    # Importazione modelli per le migrazioni
    from app.models import User, Role
    
    # Registrazione context processor per templates
    @app.context_processor
    def inject_user():
        return dict(current_user=g.get('user'))
    
    # Registrazione funzioni menu per templates
    @app.context_processor
    def inject_menu():
        from app.utils.menu import get_menu, get_menu_stats
        return dict(
            get_menu=get_menu,
            menu_stats=get_menu_stats
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


    # ==================== COMANDI CLI ====================
    
    @app.cli.command()
    def init_roles():
        """Inizializza i ruoli di default"""
        from app.models.role import Role
        Role.create_default_roles()
        print("✅ Ruoli inizializzati!")
    
    @app.cli.command()
    @click.argument('email')
    @click.argument('password')
    def create_admin(email, password):
        """Crea un utente admin"""
        from app.models.user import User
        from app.models.role import Role
        
        # Controlla se esiste già
        existing_user = User.find_by_username(email)
        if existing_user:
            print(f"❌ Utente {email} esiste già!")
            return
        
        # Crea utente
        admin_user = User(
            username=email,
            email=email,
            is_active=True,
            is_email_confirmed=True
        )
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.flush()
        
        # Assegna ruolo admin
        admin_role = Role.get_admin_role()
        if admin_role:
            admin_user.add_role(admin_role)
        
        db.session.commit()
        print(f"✅ Admin creato: {email}")
    
    @app.cli.command()
    @click.argument('email')
    def make_admin(email):
        """Rende un utente esistente admin"""
        from app.models.user import User
        from app.models.role import Role
        
        user = User.find_by_username(email)
        if not user:
            print(f"❌ Utente {email} non trovato!")
            return
        
        if user.is_admin():
            print(f"ℹ️  {email} è già admin!")
            return
        
        admin_role = Role.get_admin_role()
        if not admin_role:
            print("❌ Ruolo admin non trovato! Esegui prima 'flask init-roles'")
            return
        
        user.add_role(admin_role)
        db.session.commit()
        
        print(f"✅ {email} è ora admin!")
        print(f"   Ruoli: {', '.join(user.get_role_names())}")
    
    @app.cli.command()
    @click.argument('email')
    def remove_admin(email):
        """Rimuove il ruolo admin da un utente"""
        from app.models.user import User
        from app.models.role import Role
        
        user = User.find_by_username(email)
        if not user:
            print(f"❌ Utente {email} non trovato!")
            return
        
        if not user.is_admin():
            print(f"ℹ️  {email} non è admin!")
            return
        
        admin_role = Role.get_admin_role()
        if admin_role:
            user.remove_role(admin_role)
            db.session.commit()
            
            print(f"✅ Ruolo admin rimosso da {email}")
            print(f"   Ruoli rimanenti: {', '.join(user.get_role_names())}")
    
    @app.cli.command()
    @click.argument('email')
    @click.argument('role_name')
    def add_role(email, role_name):
        """Aggiunge un ruolo a un utente"""
        from app.models.user import User
        from app.models.role import Role
        
        user = User.find_by_username(email)
        if not user:
            print(f"❌ Utente {email} non trovato!")
            return
        
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            print(f"❌ Ruolo '{role_name}' non trovato!")
            available_roles = [r.name for r in Role.query.all()]
            print(f"   Ruoli disponibili: {', '.join(available_roles)}")
            return
        
        if user.has_role(role_name):
            print(f"ℹ️  {email} ha già il ruolo '{role_name}'!")
            return
        
        user.add_role(role)
        db.session.commit()
        
        print(f"✅ Ruolo '{role_name}' aggiunto a {email}")
        print(f"   Tutti i ruoli: {', '.join(user.get_role_names())}")
    
    @app.cli.command()
    @click.argument('email')
    @click.argument('role_name')
    def remove_role(email, role_name):
        """Rimuove un ruolo da un utente"""
        from app.models.user import User
        from app.models.role import Role
        
        user = User.find_by_username(email)
        if not user:
            print(f"❌ Utente {email} non trovato!")
            return
        
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            print(f"❌ Ruolo '{role_name}' non trovato!")
            return
        
        if not user.has_role(role_name):
            print(f"ℹ️  {email} non ha il ruolo '{role_name}'!")
            return
        
        user.remove_role(role)
        db.session.commit()
        
        print(f"✅ Ruolo '{role_name}' rimosso da {email}")
        print(f"   Ruoli rimanenti: {', '.join(user.get_role_names())}")
    
    @app.cli.command()
    def list_users():
        """Lista tutti gli utenti e i loro ruoli"""
        from app.models.user import User
        
        users = User.query.all()
        
        if not users:
            print("📭 Nessun utente registrato")
            return
        
        print(f"👥 Utenti registrati ({len(users)}):")
        print("-" * 80)
        
        for user in users:
            status_icon = "✅" if user.is_active and user.is_email_confirmed else "❌"
            admin_icon = "🔴" if user.is_admin() else ""
            roles = ', '.join(user.get_role_names()) or 'Nessun ruolo'
            
            print(f"{status_icon} {admin_icon} {user.email}")
            print(f"   Ruoli: {roles}")
            print(f"   Creato: {user.created_at.strftime('%d/%m/%Y %H:%M')}")
            if user.last_login:
                print(f"   Ultimo login: {user.last_login.strftime('%d/%m/%Y %H:%M')}")
            print()
    
    @app.cli.command()
    def list_roles():
        """Lista tutti i ruoli disponibili"""
        from app.models.role import Role
        
        roles = Role.query.all()
        
        if not roles:
            print("📭 Nessun ruolo definito. Esegui 'flask init-roles'")
            return
        
        print(f"🎭 Ruoli disponibili ({len(roles)}):")
        print("-" * 60)
        
        for role in roles:
            user_count = len(role.users)
            status = "✅" if role.is_active else "❌"
            
            print(f"{status} {role.name}")
            print(f"   Descrizione: {role.description}")
            print(f"   Utenti con questo ruolo: {user_count}")
            print(f"   Creato: {role.created_at.strftime('%d/%m/%Y %H:%M')}")
            print()
    
    return app