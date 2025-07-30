from flask import request, jsonify, render_template, redirect, url_for, flash, g
from app.models.user import User
from app.models.role import Role
from app.models.company import Company
from app.auth.decorators import admin_required, api_admin_required, moderator_required
from app import db
from app.auth.unified_decorators import unified_api_admin_required, unified_api_moderator_required
import base64
import os
from app.utils.env_manager import *
from app.logger import get_logger       
logger = get_logger(__name__)

def register_admin_routes(admin_bp):
    # ############################################################# #
    # ##################### ROUTE WEB ADMIN ####################### #
    # ############################################################# #
    
    @admin_bp.route('/dashboard')
    @admin_required
    def admin_dashboard():
        """Dashboard amministratore"""
        total_users = User.query.count()
        confirmed_users = User.query.filter_by(is_email_confirmed=True).count()
        active_users = User.query.filter_by(is_active=True).count()
        
        stats = {
            'total_users': total_users,
            'confirmed_users': confirmed_users,
            'active_users': active_users,
            'pending_confirmation': total_users - confirmed_users
        }
        
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        roles = Role.query.all()  # ← AGGIUNGI ANCHE QUESTO
        
        return render_template('admin/dashboard.html', 
                            stats=stats, 
                            recent_users=recent_users,
                            roles=roles)  # ← ASSICURATI CHE SIA QUI
    # ############## #
    # Utenti ####### #
    # ###### ####### #
    @admin_bp.route('/users')
    @admin_required
    # @moderator_required
    def manage_users():
        """Gestione utenti"""
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Filtri
        role_filter = request.args.get('role')
        status_filter = request.args.get('status')
        search = request.args.get('search', '')
        
        # Query base
        query = User.query
        
        # Applica filtri
        if search:
            query = query.filter(
                User.username.ilike(f'%{search}%') | 
                User.email.ilike(f'%{search}%')
            )
        
        if role_filter:
            role = Role.query.filter_by(name=role_filter).first()
            if role:
                query = query.filter(User.roles.contains(role))
        
        if status_filter == 'active':
            query = query.filter_by(is_active=True)
        elif status_filter == 'inactive':
            query = query.filter_by(is_active=False)
        elif status_filter == 'confirmed':
            query = query.filter_by(is_email_confirmed=True)
        elif status_filter == 'unconfirmed':
            query = query.filter_by(is_email_confirmed=False)
        
        # Paginazione
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        roles = Role.query.filter_by(is_active=True).all()
        
        # AGGIUNGI QUESTE STATISTICHE
        stats = {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'confirmed_users': User.query.filter_by(is_email_confirmed=True).count(),
            'pending_confirmation': User.query.filter_by(is_email_confirmed=False).count()
        }
        
        return render_template('admin/users.html', 
                            users=users, 
                            roles=roles,
                            stats=stats,  # ← ASSICURATI CHE SIA QUI
                            current_filters={
                                'role': role_filter,
                                'status': status_filter,
                                'search': search
                            })
    
    @admin_bp.route('/users/<string:user_uid>')
    @moderator_required
    def user_detail(user_uid):
        """Dettaglio utente"""
        user = User.query.filter_by(uid=user_uid).first_or_404()
        all_roles = Role.query.filter_by(is_active=True).all()
        
        return render_template('admin/user_detail.html', user=user, all_roles=all_roles)
    
    @admin_bp.route('/roles')
    @admin_required
    def manage_roles():
        """Gestione ruoli"""
        roles = Role.query.all()
        return render_template('admin/roles.html', roles=roles)
    

    # ############## #
    # Società ###### #
    # ###### ####### #
    @admin_bp.route('/companies')
    @admin_required
    # @moderator_required
    def manage_companies():
        """Gestione utenti"""

        
        # # Filtri
        # role_filter = request.args.get('role')
        # status_filter = request.args.get('status')
        # search = request.args.get('search', '')
        
        # # Query base
        # query = User.query
        
        # # Applica filtri
        # if search:
        #     query = query.filter(
        #         User.username.ilike(f'%{search}%') | 
        #         User.email.ilike(f'%{search}%')
        #     )
        
        # if role_filter:
        #     role = Role.query.filter_by(name=role_filter).first()
        #     if role:
        #         query = query.filter(User.roles.contains(role))
        
        # if status_filter == 'active':
        #     query = query.filter_by(is_active=True)
        # elif status_filter == 'inactive':
        #     query = query.filter_by(is_active=False)
        # elif status_filter == 'confirmed':
        #     query = query.filter_by(is_email_confirmed=True)
        # elif status_filter == 'unconfirmed':
        #     query = query.filter_by(is_email_confirmed=False)
        
        # # Paginazione
        # users = query.order_by(User.created_at.desc()).paginate(
        #     page=page, per_page=per_page, error_out=False
        # )
        
        # roles = Role.query.filter_by(is_active=True).all()
        
        # # AGGIUNGI QUESTE STATISTICHE
        # stats = {
        #     'total_users': User.query.count(),
        #     'active_users': User.query.filter_by(is_active=True).count(),
        #     'confirmed_users': User.query.filter_by(is_email_confirmed=True).count(),
        #     'pending_confirmation': User.query.filter_by(is_email_confirmed=False).count()
        # }
        companies =  Company.query.all() 
        return render_template('admin/companies.html', 
                            companies=companies, 
                            # roles=roles,
                            # stats=stats,  # ← ASSICURATI CHE SIA QUI
                            # current_filters={
                            #     'role': role_filter,
                            #     'status': status_filter,
                            #     'search': search
                            # }
    )  

    