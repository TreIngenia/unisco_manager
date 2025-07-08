from flask import request, jsonify, render_template, redirect, url_for, flash, g
from app.models.user import User
from app.models.role import Role
from app.auth.decorators import admin_required, api_admin_required, moderator_required
from app import db

def register_admin_routes(admin_bp):
    
    # ==================== ROUTE WEB ADMIN ====================
    
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
        
        return render_template('admin/dashboard.html', stats=stats, recent_users=recent_users)
    
    @admin_bp.route('/users')
    @moderator_required
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
        
        return render_template('admin/users.html', 
                             users=users, 
                             roles=roles,
                             current_filters={
                                 'role': role_filter,
                                 'status': status_filter,
                                 'search': search
                             })
    
    @admin_bp.route('/users/<int:user_id>')
    @moderator_required
    def user_detail(user_id):
        """Dettaglio utente"""
        user = User.query.get_or_404(user_id)
        all_roles = Role.query.filter_by(is_active=True).all()
        
        return render_template('admin/user_detail.html', user=user, all_roles=all_roles)
    
    @admin_bp.route('/roles')
    @admin_required
    def manage_roles():
        """Gestione ruoli"""
        roles = Role.query.all()
        return render_template('admin/roles.html', roles=roles)
    
    # ==================== API ADMIN ====================
    
    @admin_bp.route('/api/users/<int:user_id>/toggle-status', methods=['POST'])
    @api_admin_required
    def toggle_user_status(user_id):
        """Attiva/Disattiva utente"""
        user = User.query.get_or_404(user_id)
        
        # Non permettere di disattivare se stesso
        if user.id == g.current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Non puoi disattivare te stesso!'
            }), 400
        
        user.is_active = not user.is_active
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Utente {"attivato" if user.is_active else "disattivato"} con successo',
            'is_active': user.is_active
        })
    
    @admin_bp.route('/api/users/<int:user_id>/roles', methods=['POST'])
    @api_admin_required
    def update_user_roles(user_id):
        """Aggiorna ruoli utente"""
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data or 'role_ids' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Lista role_ids richiesta'
            }), 400
        
        # Non permettere di modificare i propri ruoli
        if user.id == g.current_user.id:
            return jsonify({
                'status': 'error',
                'message': 'Non puoi modificare i tuoi ruoli!'
            }), 400
        
        # Verifica che tutti i ruoli esistano
        role_ids = data['role_ids']
        roles = Role.query.filter(Role.id.in_(role_ids)).all()
        
        if len(roles) != len(role_ids):
            return jsonify({
                'status': 'error',
                'message': 'Alcuni ruoli specificati non esistono'
            }), 400
        
        # Aggiorna ruoli
        user.roles = roles
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Ruoli aggiornati con successo',
            'user': user.to_dict(include_roles=True)
        })
    
    @admin_bp.route('/api/users/<int:user_id>/add-role', methods=['POST'])
    @api_admin_required
    def add_user_role(user_id):
        """Aggiunge ruolo a utente"""
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data or 'role_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'role_id richiesto'
            }), 400
        
        role = Role.query.get_or_404(data['role_id'])
        
        if role in user.roles:
            return jsonify({
                'status': 'error',
                'message': f'L\'utente ha già il ruolo {role.name}'
            }), 400
        
        user.add_role(role)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Ruolo {role.name} aggiunto con successo',
            'user': user.to_dict(include_roles=True)
        })
    
    @admin_bp.route('/api/users/<int:user_id>/remove-role', methods=['POST'])
    @api_admin_required
    def remove_user_role(user_id):
        """Rimuove ruolo da utente"""
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data or 'role_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'role_id richiesto'
            }), 400
        
        role = Role.query.get_or_404(data['role_id'])
        
        # Non permettere di rimuovere admin da se stesso
        if user.id == g.current_user.id and role.name == 'admin':
            return jsonify({
                'status': 'error',
                'message': 'Non puoi rimuovere il ruolo admin da te stesso!'
            }), 400
        
        if role not in user.roles:
            return jsonify({
                'status': 'error',
                'message': f'L\'utente non ha il ruolo {role.name}'
            }), 400
        
        user.remove_role(role)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Ruolo {role.name} rimosso con successo',
            'user': user.to_dict(include_roles=True)
        })
    
    @admin_bp.route('/api/roles', methods=['GET'])
    @api_admin_required
    def get_roles():
        """Lista tutti i ruoli"""
        roles = Role.query.all()
        return jsonify([role.to_dict() for role in roles])
    
    @admin_bp.route('/api/roles', methods=['POST'])
    @api_admin_required
    def create_role():
        """Crea nuovo ruolo"""
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({
                'status': 'error',
                'message': 'Nome ruolo richiesto'
            }), 400
        
        # Controlla se esiste già
        existing_role = Role.query.filter_by(name=data['name']).first()
        if existing_role:
            return jsonify({
                'status': 'error',
                'message': 'Ruolo già esistente'
            }), 409
        
        role = Role(
            name=data['name'],
            description=data.get('description', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Ruolo creato con successo',
            'role': role.to_dict()
        }), 201
    
    @admin_bp.route('/api/users/stats', methods=['GET'])
    @api_admin_required
    def get_user_stats():
        """Statistiche utenti"""
        stats = {
            'total_users': User.query.count(),
            'active_users': User.query.filter_by(is_active=True).count(),
            'confirmed_users': User.query.filter_by(is_email_confirmed=True).count(),
            'admins': len(User.get_admins()),
            'users_by_role': {}
        }
        
        # Conta utenti per ruolo
        roles = Role.query.all()
        for role in roles:
            stats['users_by_role'][role.name] = len(role.users)
        
        return jsonify(stats)