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

def register_cli_commands(app):
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