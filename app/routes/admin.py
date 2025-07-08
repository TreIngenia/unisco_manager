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
        roles = Role.query.all()  # ← AGGIUNGI ANCHE QUESTO
        
        return render_template('admin/dashboard.html', 
                            stats=stats, 
                            recent_users=recent_users,
                            roles=roles)  # ← ASSICURATI CHE SIA QUI
    
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
    
    @admin_bp.route('/api/users', methods=['POST'])
    @api_admin_required
    def create_user():
        """Crea nuovo utente"""
        data = request.get_json()
        
        # Validazione dati
        if not data or not data.get('username') or not data.get('email'):
            return jsonify({
                'status': 'error',
                'message': 'Username e email sono obbligatori'
            }), 400
        
        if not data.get('password'):
            return jsonify({
                'status': 'error',
                'message': 'Password è obbligatoria'
            }), 400
        
        # Controlla se username esiste già
        existing_user = User.find_by_username(data['username'])
        if existing_user:
            return jsonify({
                'status': 'error',
                'message': 'Username già esistente'
            }), 409
        
        # Controlla se email esiste già
        existing_email = User.find_by_email(data['email'])
        if existing_email:
            return jsonify({
                'status': 'error',
                'message': 'Email già esistente'
            }), 409
        
        try:
            # Crea nuovo utente
            user = User(
                username=data['username'],
                email=data['email'],
                is_active=data.get('is_active', True),
                is_email_confirmed=data.get('is_email_confirmed', False)
            )
            user.set_password(data['password'])
            
            db.session.add(user)
            db.session.flush()
            
            # Assegna ruoli
            if data.get('roles'):
                roles = Role.query.filter(Role.id.in_(data['roles'])).all()
                for role in roles:
                    user.add_role(role)
            else:
                # Assegna ruolo default
                default_role = Role.get_default_role()
                if default_role:
                    user.add_role(default_role)
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Utente creato con successo',
                'user': user.to_dict(include_roles=True)
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Errore nella creazione utente: {str(e)}'
            }), 500

    @admin_bp.route('/api/users/<int:user_id>', methods=['GET'])
    @api_admin_required
    def get_user_api(user_id):
        """Ottieni dettagli utente"""
        user = User.query.get_or_404(user_id)
        return jsonify(user.to_dict(include_roles=True))

    @admin_bp.route('/api/users/<int:user_id>', methods=['PUT'])
    @api_admin_required
    def update_user(user_id):
        """Aggiorna utente"""
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Dati richiesti'
            }), 400
        
        try:
            # Aggiorna username se fornito
            if 'username' in data and data['username'] != user.username:
                existing_user = User.find_by_username(data['username'])
                if existing_user and existing_user.id != user.id:
                    return jsonify({
                        'status': 'error',
                        'message': 'Username già esistente'
                    }), 409
                user.username = data['username']
            
            # Aggiorna email se fornita
            if 'email' in data and data['email'] != user.email:
                existing_user = User.find_by_email(data['email'])
                if existing_user and existing_user.id != user.id:
                    return jsonify({
                        'status': 'error',
                        'message': 'Email già esistente'
                    }), 409
                user.email = data['email']
            
            # Aggiorna status
            if 'is_active' in data:
                # Non permettere di disattivare se stesso
                if user.id == g.user.id and not data['is_active']:
                    return jsonify({
                        'status': 'error',
                        'message': 'Non puoi disattivare te stesso'
                    }), 400
                user.is_active = data['is_active']
            
            if 'is_email_confirmed' in data:
                user.is_email_confirmed = data['is_email_confirmed']
            
            # Aggiorna ruoli
            if 'roles' in data:
                # Non permettere di modificare i propri ruoli
                if user.id == g.user.id:
                    return jsonify({
                        'status': 'error',
                        'message': 'Non puoi modificare i tuoi ruoli'
                    }), 400
                
                # Rimuovi tutti i ruoli attuali
                user.roles.clear()
                
                # Assegna nuovi ruoli
                if data['roles']:
                    roles = Role.query.filter(Role.id.in_(data['roles'])).all()
                    for role in roles:
                        user.add_role(role)
                else:
                    # Assegna ruolo default se nessun ruolo specificato
                    default_role = Role.get_default_role()
                    if default_role:
                        user.add_role(default_role)
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Utente aggiornato con successo',
                'user': user.to_dict(include_roles=True)
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Errore nell\'aggiornamento: {str(e)}'
            }), 500

    @admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
    @api_admin_required
    def delete_user(user_id):
        """Elimina utente"""
        user = User.query.get_or_404(user_id)
        
        # Non permettere di eliminare se stesso
        if user.id == g.user.id:
            return jsonify({
                'status': 'error',
                'message': 'Non puoi eliminare te stesso'
            }), 400
        
        # Non permettere di eliminare altri admin (opzionale)
        if user.is_admin():
            return jsonify({
                'status': 'error',
                'message': 'Non puoi eliminare un amministratore'
            }), 400
        
        try:
            # Rimuovi tutte le associazioni con i ruoli
            user.roles.clear()
            
            # Elimina utente
            db.session.delete(user)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Utente eliminato con successo'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Errore nell\'eliminazione: {str(e)}'
            }), 500

    @admin_bp.route('/api/users/export', methods=['GET'])
    @api_admin_required
    def export_users():
        """Esporta utenti in CSV"""
        import csv
        from io import StringIO
        from flask import make_response
        
        # Ottieni lista utenti da esportare
        user_ids = request.args.getlist('user_ids')
        
        if user_ids:
            # Esporta solo utenti selezionati
            users = User.query.filter(User.id.in_(user_ids)).all()
        else:
            # Esporta tutti gli utenti
            users = User.query.all()
        
        # Crea CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'ID',
            'Username',
            'Email',
            'Ruoli',
            'Attivo',
            'Email Confermata',
            'Data Registrazione',
            'Ultimo Accesso'
        ])
        
        # Dati
        for user in users:
            writer.writerow([
                user.id,
                user.username,
                user.email,
                ', '.join([role.name for role in user.roles]),
                'Sì' if user.is_active else 'No',
                'Sì' if user.is_email_confirmed else 'No',
                user.created_at.strftime('%d/%m/%Y %H:%M') if user.created_at else '',
                user.last_login.strftime('%d/%m/%Y %H:%M') if user.last_login else 'Mai'
            ])
        
        # Crea response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=utenti.csv'
        
        return response

    @admin_bp.route('/api/users/search', methods=['GET'])
    @api_admin_required
    def search_users():
        """Ricerca utenti"""
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify([])
        
        users = User.query.filter(
            User.username.ilike(f'%{query}%') |
            User.email.ilike(f'%{query}%')
        ).limit(limit).all()
        
        return jsonify([{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active
        } for user in users])
    
    @admin_bp.route('/api/users/bulk-action', methods=['POST'])
    @api_admin_required
    def bulk_user_action():
        """Azioni multiple sugli utenti"""
        data = request.get_json()
        
        if not data or not data.get('action') or not data.get('user_ids'):
            return jsonify({
                'status': 'error',
                'message': 'Azione e lista utenti richieste'
            }), 400
        
        action = data['action']
        user_ids = data['user_ids']
        
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        if not users:
            return jsonify({
                'status': 'error',
                'message': 'Nessun utente trovato'
            }), 404
        
        try:
            results = []
            
            for user in users:
                # Non permettere azioni su se stesso
                if user.id == g.user.id:
                    results.append({
                        'user_id': user.id,
                        'status': 'skipped',
                        'message': 'Non puoi modificare te stesso'
                    })
                    continue
                
                if action == 'toggle_status':
                    user.is_active = not user.is_active
                    results.append({
                        'user_id': user.id,
                        'status': 'success',
                        'message': f'Utente {"attivato" if user.is_active else "disattivato"}'
                    })
                    
                elif action == 'activate':
                    user.is_active = True
                    results.append({
                        'user_id': user.id,
                        'status': 'success',
                        'message': 'Utente attivato'
                    })
                    
                elif action == 'deactivate':
                    user.is_active = False
                    results.append({
                        'user_id': user.id,
                        'status': 'success',
                        'message': 'Utente disattivato'
                    })
                    
                elif action == 'delete':
                    # Non eliminare admin
                    if user.is_admin():
                        results.append({
                            'user_id': user.id,
                            'status': 'skipped',
                            'message': 'Non puoi eliminare un amministratore'
                        })
                        continue
                    
                    # Rimuovi ruoli e elimina
                    user.roles.clear()
                    db.session.delete(user)
                    results.append({
                        'user_id': user.id,
                        'status': 'success',
                        'message': 'Utente eliminato'
                    })
                    
                else:
                    results.append({
                        'user_id': user.id,
                        'status': 'error',
                        'message': 'Azione non valida'
                    })
            
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': f'Azione "{action}" completata',
                'results': results
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Errore nell\'azione: {str(e)}'
            }), 500

    @admin_bp.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
    @api_admin_required
    def reset_user_password(user_id):
        """Reset password utente (solo admin)"""
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data or not data.get('new_password'):
            return jsonify({
                'status': 'error',
                'message': 'Nuova password richiesta'
            }), 400
        
        new_password = data['new_password']
        
        if len(new_password) < 8:
            return jsonify({
                'status': 'error',
                'message': 'La password deve essere di almeno 8 caratteri'
            }), 400
        
        try:
            user.set_password(new_password)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Password utente reimpostata con successo'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Errore nel reset password: {str(e)}'
            }), 500

    @admin_bp.route('/api/users/<int:user_id>/send-welcome', methods=['POST'])
    @api_admin_required
    def send_welcome_email(user_id):
        """Invia email di benvenuto"""
        user = User.query.get_or_404(user_id)
        
        try:
            # Qui dovresti implementare l'invio dell'email di benvenuto
            # send_welcome_email(user)
            
            return jsonify({
                'status': 'success',
                'message': 'Email di benvenuto inviata con successo'
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Errore nell\'invio email: {str(e)}'
            }), 500    