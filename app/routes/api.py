from flask import request, jsonify, render_template, redirect, url_for, flash, g
from app.models.user import User
from app.models.role import Role
from app.models.company import Company
from app.auth.decorators import admin_required, api_admin_required, moderator_required
from app import db
from app.auth.unified_decorators import unified_api_admin_required, unified_api_moderator_required
import base64
import os
from datetime import datetime
from app.utils.env_manager import *
from app.logger import get_logger       
from app.voip_cdr.cdr_categories import CDRAnalyticsEnhanced

logger = get_logger(__name__)


def register_api_routes(api_bp):
    # ####################### #
    # USER ################## #
    # #### ################## #

    # Informazioni statistiche generiche tutti sugli utenti inseriti 
    @api_bp.route('/users/stats', methods=['GET'])
    # @api_admin_required
    @unified_api_admin_required
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
    

    # Informazioni di un utente passando UID
    @api_bp.route('/users/<string:user_uid>', methods=['GET'])
    # @api_admin_required
    @unified_api_admin_required
    def get_user_api(user_uid):
        """Ottieni dettagli utente"""
        user = User.query.filter_by(uid=user_uid).first_or_404()
        return jsonify(user.to_dict(include_roles=True))
    
    # Elenco completo utenti
    @api_bp.route('/users', methods=['GET'])
    # @api_admin_required
    @unified_api_admin_required    
    def get_users_api():
        """Ottieni dettagli utente"""
        users = User.query.all()
        return jsonify([user.to_dict(include_roles=True) for user in users])

    # Crea utente
    @api_bp.route('/users', methods=['POST'])
    # @api_admin_required
    @unified_api_admin_required
    def create_user():
        """Crea un nuovo utente - VERSIONE COMPLETA"""
        data = request.get_json()

        if not data:
            return jsonify({'status': 'error', 'message': 'Dati richiesti'}), 400

        try:
            # ==================== VALIDAZIONE CAMPI UNICI ====================
            # if User.find_by_username(data.get('email')):
            #     return jsonify({'status': 'error', 'message': 'Username già esistente'}), 409

            if User.find_by_email(data.get('email')):
                return jsonify({'status': 'error', 'message': 'Email già esistente'}), 409

            if 'password' not in data or len(data['password']) < 8:
                return jsonify({'status': 'error', 'message': 'Password mancante o troppo corta'}), 400

            # ==================== CREAZIONE UTENTE ====================
            user = User(
                username=data['email'].strip(),
                email=data['email'].strip(),
                first_name=data.get('first_name', '').strip() or None,
                last_name=data.get('last_name', '').strip() or None,
                phone=data.get('phone', '').strip() or None,
                is_active=bool(data.get('is_active', True)),
                is_email_confirmed=bool(data.get('is_email_confirmed', False))
            )

            user.set_password(data['password'])

            # ==================== RUOLI ====================
            if 'roles' in data and data['roles']:
                role_ids = [int(role_id) for role_id in data['roles']]
                roles = Role.query.filter(Role.id.in_(role_ids)).all()
                if len(roles) != len(role_ids):
                    return jsonify({'status': 'error', 'message': 'Alcuni ruoli non validi'}), 400
                for role in roles:
                    user.add_role(role)
            else:
                default_role = Role.get_default_role()
                if default_role:
                    user.add_role(default_role)

            # ==================== AVATAR ====================
            base64_data = data.get('base64_avatar')
            if base64_data and base64_data not in ['null', 'undefined']:
                upload_folder = os.path.join(AVATAR_FOLDER)
                os.makedirs(upload_folder, exist_ok=True)
                filename = user.uid + '.jpg'
                filepath = os.path.join(upload_folder, filename)

                if ',' in base64_data:
                    base64_data = base64_data.split(',')[1]

                base64_data += '=' * ((4 - len(base64_data) % 4) % 4)
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(base64_data))
                user.profile_image = filename
            else:
                user.profile_image = None

            # ==================== COMPANY ====================
            if 'company' in data:
                company_values = data['company']
                if isinstance(company_values, list) and company_values:
                    company_uid = company_values[0]
                    company = Company.query.filter_by(uid=company_uid).first()
                    if not company:
                        return jsonify({'status': 'error', 'message': 'Company non trovata'}), 404
                    user.company = company

            # ==================== COMMIT ====================
            db.session.add(user)
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': 'Utente creato con successo',
                'user': user.to_dict(include_roles=True)
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Errore durante la creazione: {str(e)}'
            }), 500


    # Aggiorna utente    
    @api_bp.route('/users/<string:user_uid>', methods=['PUT'])
    @unified_api_admin_required  # Usa il decoratore unificato
    def update_user(user_uid):
        """Aggiorna utente - VERSIONE COMPLETA"""
        user = User.query.filter_by(uid=user_uid).first_or_404()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Dati richiesti'
            }), 400
        
        try:
            # ==================== DATI PERSONALI ====================
            if 'first_name' in data:
                user.first_name = data['first_name'].strip() if data['first_name'] else None
            
            if 'last_name' in data:
                user.last_name = data['last_name'].strip() if data['last_name'] else None
            
            if 'phone' in data:
                user.phone = data['phone'].strip() if data['phone'] else None
            
            # ==================== CREDENZIALI ====================
            # Aggiorna username se fornito e diverso
            if 'username' in data and data['username'] != user.username:
                existing_user = User.find_by_username(data['username'])
                if existing_user and existing_user.uid != user.uid:
                    return jsonify({
                        'status': 'error',
                        'message': 'Username già esistente'
                    }), 409
                user.username = data['username'].strip()
            
            # Aggiorna email se fornita e diversa
            if 'email' in data and data['email'] != user.email:
                existing_user = User.find_by_email(data['email'])
                if existing_user and existing_user.uid != user.uid:
                    return jsonify({
                        'status': 'error',
                        'message': 'Email già esistente'
                    }), 409
                user.email = data['email'].strip()
            
            # Aggiorna password se fornita
            if 'password' in data and data['password']:
                if len(data['password']) < 8:
                    return jsonify({
                        'status': 'error',
                        'message': 'Password deve essere di almeno 8 caratteri'
                    }), 400
                user.set_password(data['password'])
            
            # ==================== STATUS ACCOUNT ====================
            if 'is_active' in data:
                # Non permettere di disattivare se stesso
                if user.uid == g.current_user.uid and not data['is_active']:
                    return jsonify({
                        'status': 'error',
                        'message': 'Non puoi disattivare te stesso'
                    }), 400
                user.is_active = bool(data['is_active'])
            else:
                user.is_active = False
            
            if 'is_email_confirmed' in data:
                user.is_email_confirmed = bool(data['is_email_confirmed'])
            else:
                user.is_email_confirmed = False    
            
            # ==================== GESTIONE RUOLI ====================
            if 'roles' in data:
                # Non permettere di modificare i propri ruoli
                # if user.uid == g.current_user.uid:
                #     return jsonify({
                #         'status': 'error',
                #         'message': 'Non puoi modificare i tuoi ruoli'
                #     }), 400
                
                # Rimuovi tutti i ruoli attuali
                user.roles.clear()
                
                # Assegna nuovi ruoli
                if data['roles']:  # Se ci sono ruoli da assegnare
                    # Verifica che tutti i ruoli esistano
                    role_ids = [int(role_id) for role_id in data['roles']]
                    roles = Role.query.filter(Role.id.in_(role_ids)).all()
                    
                    if len(roles) != len(role_ids):
                        return jsonify({
                            'status': 'error',
                            'message': 'Alcuni ruoli specificati non esistono'
                        }), 400
                    
                    # Assegna i ruoli
                    for role in roles:
                        user.add_role(role)
                else:
                    # Se nessun ruolo specificato, assegna ruolo default
                    default_role = Role.get_default_role()
                    if default_role:
                        user.add_role(default_role)
            
            if not data.get('base64_avatar') or data['base64_avatar'] in ['null', 'undefined']:
                user.profile_image = None
                
            else:
                base64_data = data['base64_avatar']
                if base64_data:
                    upload_folder = os.path.join(AVATAR_FOLDER)
                    os.makedirs(upload_folder, exist_ok=True)
                    print(upload_folder)
                    filename = data["uid"] + '.jpg'
                    filepath = os.path.join(upload_folder, filename)

                    if ',' in base64_data:
                        base64_data = base64_data.split(',')[1]

                    with open(filepath, 'wb') as f:
                        f.write(base64.b64decode(base64_data))
                    print(filename)
                    user.profile_image = filename
                else:
                    user.profile_image = None

            if 'company' in data:
                company_values = data['company']
                if isinstance(company_values, list) and company_values:
                    company_uid = company_values[0]
                    company = Company.query.filter_by(uid=company_uid).first()
                    if not company:
                        return jsonify({'status': 'error', 'message': 'Società non trovata'}), 404
                    user.company = company
                else:
                    user.company = None


            # Salva le modifiche
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

    # Elimina utente
    @api_bp.route('/users/<string:user_uid>', methods=['DELETE'])
    # @api_admin_required
    @unified_api_admin_required
    def delete_user(user_uid):
        """Elimina utente"""
        user = User.query.filter_by(uid=user_uid).first_or_404()
        
        # Non permettere di eliminare se stesso
        if user.uid == g.user.uid:
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

    # Esporta informazioni di tutti gli utente
    @api_bp.route('/users/export', methods=['GET'])
    # @api_admin_required
    @unified_api_admin_required
    def export_users():
        """Esporta utenti in CSV"""
        import csv
        from io import StringIO
        from flask import make_response
        
        # Ottieni lista utenti da esportare
        user_uids = request.args.getlist('user_uids')
        
        if user_uids:
            # Esporta solo utenti selezionati
            users = User.query.filter(user.uid.in_(user_uids)).all()
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
                user.uid,
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

    # Esegue una richierca passando il parametro q=username o q=email e limit=1
    @api_bp.route('/users/search', methods=['GET'])
    # @api_admin_required
    @unified_api_admin_required
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
            'id': user.uid,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active
        } for user in users])
    
    # Da capire
    @api_bp.route('/users/bulk-action', methods=['POST'])
    # @api_admin_required
    @unified_api_admin_required
    def bulk_user_action():
        """Azioni multiple sugli utenti"""
        data = request.get_json()
        
        if not data or not data.get('action') or not data.get('user_uids'):
            return jsonify({
                'status': 'error',
                'message': 'Azione e lista utenti richieste'
            }), 400
        
        action = data['action']
        user_uids = data['user_uids']
        
        users = User.query.filter(user.uid.in_(user_uids)).all()
        
        if not users:
            return jsonify({
                'status': 'error',
                'message': 'Nessun utente trovato'
            }), 404
        
        try:
            results = []
            
            for user in users:
                # Non permettere azioni su se stesso
                if user.uid == g.user.uid:
                    results.append({
                        'user_uid': user.uid,
                        'status': 'skipped',
                        'message': 'Non puoi modificare te stesso'
                    })
                    continue
                
                if action == 'toggle_status':
                    user.is_active = not user.is_active
                    results.append({
                        'user_uid': user.uid,
                        'status': 'success',
                        'message': f'Utente {"attivato" if user.is_active else "disattivato"}'
                    })
                    
                elif action == 'activate':
                    user.is_active = True
                    results.append({
                        'user_uid': user.uid,
                        'status': 'success',
                        'message': 'Utente attivato'
                    })
                    
                elif action == 'deactivate':
                    user.is_active = False
                    results.append({
                        'user_uid': user.uid,
                        'status': 'success',
                        'message': 'Utente disattivato'
                    })
                    
                elif action == 'delete':
                    # Non eliminare admin
                    if user.is_admin():
                        results.append({
                            'user_uid': user.uid,
                            'status': 'skipped',
                            'message': 'Non puoi eliminare un amministratore'
                        })
                        continue
                    
                    # Rimuovi ruoli e elimina
                    user.roles.clear()
                    db.session.delete(user)
                    results.append({
                        'user_uid': user.uid,
                        'status': 'success',
                        'message': 'Utente eliminato'
                    })
                    
                else:
                    results.append({
                        'user_uid': user.uid,
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


    #Cambio password
    @api_bp.route('/users/<string:user_uid>/reset-password', methods=['POST'])
    # @api_admin_required
    @unified_api_admin_required
    def reset_user_password(user_uid):
        """Reset password utente (solo admin)"""
        user = User.query.filter_by(uid=user_uid).first_or_404()
        data = request.get_json()
        
        if not data or not data.get('password'):
            return jsonify({
                'status': 'error',
                'message': 'Password richiesta'
            }), 400
        
        new_password = data['password']
        confirm_password = data['confirm_password']

        if new_password != confirm_password:
            return jsonify({
                'status': 'error',
                'message': 'La password e la password di conferma non sono uguali.'
            }), 400
        
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

    # Invia il messaggio di benventuto
    @api_bp.route('/users/<string:user_uid>/send-welcome', methods=['POST'])
    # @api_admin_required
    @unified_api_admin_required
    def send_welcome_email(user_uid):
        """Invia email di benvenuto"""
        user = User.query.filter_by(uid=user_uid).first_or_404()
        
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
        
    @api_bp.route('/users/<string:user_uid>/toggle-status', methods=['POST'])
    # @api_admin_required
    @unified_api_admin_required
    def toggle_user_status(user_uid):
        """Attiva/Disattiva utente"""
        user = User.query.filter_by(uid=user_uid).first_or_404()
        
        # Non permettere di disattivare se stesso
        if user.uid == g.current_user.uid:
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
    
    @api_bp.route('/users/<string:user_uid>/roles', methods=['POST'])
    # @api_admin_required
    @unified_api_admin_required
    def update_user_roles(user_uid):
        """Aggiorna ruoli utente"""
        user = User.query.filter_by(uid=user_uid).first_or_404()
        data = request.get_json()
        
        if not data or 'role_ids' not in data:
            return jsonify({
                'status': 'error',
                'message': 'Lista role_ids richiesta'
            }), 400
        
        # Non permettere di modificare i propri ruoli
        if user.uid == g.current_user.uid:
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
    
    @api_bp.route('/users/<string:user_uid>/add-role', methods=['POST'])
    # @api_admin_required
    @unified_api_admin_required
    def add_user_role(user_uid):
        """Aggiunge ruolo a utente"""
        user = User.query.filter_by(uid=user_uid).first_or_404()
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
    
    @api_bp.route('/users/<int:user_uid>/remove-role', methods=['POST'])
    # @api_admin_required
    @unified_api_admin_required
    def remove_user_role(user_uid):
        """Rimuove ruolo da utente"""
        user = User.query.filter_by(uid=user_uid).first_or_404()
        data = request.get_json()
        
        if not data or 'role_id' not in data:
            return jsonify({
                'status': 'error',
                'message': 'role_id richiesto'
            }), 400
        
        role = Role.query.get_or_404(data['role_id'])
        
        # Non permettere di rimuovere admin da se stesso
        if user.uid == g.current_user.uid and role.name == 'admin':
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
    
    # ####################### #
    # ROLES ################# #
    # #### ################## #
    @api_bp.route('/roles', methods=['GET'])
    # @api_admin_required
    @unified_api_admin_required
    def get_roles():
        """Lista tutti i ruoli"""
        roles = Role.query.all()
        return jsonify([role.to_dict() for role in roles])
    

    @api_bp.route('/roles', methods=['POST'])
    # @api_admin_required
    @unified_api_admin_required
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
    
    # ####################### #
    # COMPANY ############### #
    # #### ################## #  

    # Elenco completo società
    @api_bp.route('/companies', methods=['GET'])
    # @api_admin_required
    @unified_api_admin_required
    def get_compananies_api():
        """Ottieni dettagli società"""
        # companies = Company.query.all()
        # result = []

        # for company in companies:
        #     company_data = company.to_dict()

        #     # Aggiungi la proprietà `related_children_summary`
        #     company_data['related_children'] = company.related_children_summary

        #     result.append(company_data)

        # return jsonify(result)
        result = Company.get_companies_with_related_summary()
        return jsonify(result)
        
        companies = Company.query.all()
        return jsonify([company.to_dict() for company in companies])
    
    # Restituisce le società per select2
    @api_bp.route('/companies/select2', methods=['GET'])
    # @api_admin_required
    @unified_api_admin_required
    def get_companies_select2():
        results = Company.get_all_for_select()
        return jsonify(results)

    # Restituisce società di un uid specifico
    @api_bp.route('/company/<string:uid>', methods=['GET'])
    # @unified_api_admin_required
    # @api_admin_required
    @unified_api_admin_required
    def get_company_api(uid):
        company = Company.query.filter_by(uid=uid).first_or_404()

        # Ottieni i dati base della company
        company_data = company.to_dict()

        # Integra i dati dei collegamenti
        company_data['related_children'] = Company.find_related_companies_summary_for_select(uid)

        return jsonify({
            'status': 'success',
            'company': company_data
    })
    
    
    # Crea socieà
    @api_bp.route('/company', methods=['POST'])
    # @api_admin_required
    @unified_api_admin_required
    def create_company():
        """Crea un nuovo utente - VERSIONE COMPLETA"""
        data = request.get_json()

        if not data:
            return jsonify({'status': 'error', 'message': 'Dati richiesti'}), 400

        try:
            # ==================== VALIDAZIONE CAMPI UNICI ====================
            if Company.find_by_name(data.get('nome_societa')):
                return jsonify({'status': 'error', 'message': 'Società già esistente'}), 409

            if Company.find_by_e_mail(data.get('e_mail')):
                return jsonify({'status': 'error', 'message': 'Email già esistente'}), 409


            # ==================== CREAZIONE UTENTE ====================
            data_db = Company(
                nome_societa=data['nome_societa'].strip(),
                partita_iva=data['partita_iva'].strip() or None,
                codice_fiscale=data['codice_fiscale'].strip() or None,
                indirizzo=data['indirizzo'].strip() or None,
                cap=data['cap'].strip() or None,
                citta=data['citta'].strip() or None,
                telefono=data['telefono'].strip() or None,
                fax=data['fax'].strip() or None,
                e_mail=data['e_mail'].strip(),
                pec=data['pec'].strip() or None,
                sito_web=data['sito_web'].strip() or None,
                # username=data['email'].strip() or None,
                # username=data['email'].strip()or None ,
                # username=data['email'].strip()or None ,

                # email=data['email'].strip(),
                # first_name=data.get('first_name', '').strip() or None,
                # last_name=data.get('last_name', '').strip() or None,
                # phone=data.get('phone', '').strip() or None,
                is_active=bool(data.get('is_active', False)),
                societa_principale=bool(data.get('societa_principale', False))
            )

            if 'societa_collegate' in data:
                related_uids = data['societa_collegate']
                if isinstance(related_uids, list):
                    related_companies = Company.query.filter(Company.uid.in_(related_uids)).all()

                    # Pulisce le attuali relazioni e aggiorna con le nuove
                    data_db.related_companies = related_companies
                else:
                    data_db.related_companies = []

            base64_data = data.get('base64_avatar')
            if base64_data and base64_data not in ['null', 'undefined']:
                upload_folder = os.path.join(AVATAR_FOLDER)
                os.makedirs(upload_folder, exist_ok=True)
                filename = data_db.uid + '.jpg'
                filepath = os.path.join(upload_folder, filename)

                if ',' in base64_data:
                    base64_data = base64_data.split(',')[1]

                base64_data += '=' * ((4 - len(base64_data) % 4) % 4)
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(base64_data))
                data_db.profile_image = filename
            else:
                data_db.profile_image = None

            # ==================== COMPANY ====================
            if 'societa_di_riferimento' in data:
                company_values = data['societa_di_riferimento']
                if isinstance(company_values, list) and company_values:
                    company_uid = company_values[0]
                    company = Company.query.filter_by(uid=company_uid).first()
                    # if not company:
                    #     return jsonify({'status': 'error', 'message': 'Company non trovata'}), 404
                    data_db.societa_di_riferimento = company

            # ==================== COMMIT ====================
            db.session.add(data_db)
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': 'Utente creato con successo',
                'user': data_db.to_dict()
            })

        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Errore durante la creazione: {str(e)}'
            }), 500
        

    # Aggiorna societa    
    @api_bp.route('/company/<string:uid_change>', methods=['PUT'])
    @unified_api_admin_required  # Usa il decoratore unificato
    def update_company(uid_change):
        
        """Aggiorna utente - VERSIONE COMPLETA"""
        data_db = Company.query.filter_by(uid=uid_change).first_or_404()
        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Dati richiesti'
            }), 400
        
        try:
            # ==================== DATI PERSONALI ====================
            if 'nome_societa' in data:
                data_db.nome_societa = data['nome_societa'].strip() if data['nome_societa'] else None
            
            if 'partita_iva' in data:
                data_db.partita_iva = data['partita_iva'].strip() if data['partita_iva'] else None
            
            if 'codice_fiscale' in data:
                data_db.codice_fiscale = data['codice_fiscale'].strip() if data['codice_fiscale'] else None

            if 'indirizzo' in data:
                data_db.indirizzo = data['indirizzo'].strip() if data['indirizzo'] else None
            
            if 'cap' in data:
                data_db.cap = data['cap'].strip() if data['cap'] else None
            
            if 'citta' in data:
                data_db.citta = data['citta'].strip() if data['citta'] else None

            if 'telefono' in data:
                data_db.telefono = data['telefono'].strip() if data['telefono'] else None

            if 'fax' in data:
                data_db.fax = data['fax'].strip() if data['fax'] else None

            # if 'e_mail' in data:
            #     data_db.e_mail = data['e_mail'].strip() if data['e_mail'] else None

            if 'pec' in data:
                data_db.pec = data['pec'].strip() if data['pec'] else None

            if 'sito_web' in data:
                data_db.sito_web = data['sito_web'].strip() if data['sito_web'] else None

            if 'societa_principale' in data:
                data_db.societa_principale = bool(data['societa_principale']) if data['societa_principale'] else False
            
            
            # ==================== CREDENZIALI ====================
            # # Aggiorna username se fornito e diverso
            # if 'username' in data and data['username'] != data_db.username:
            #     existing_user = User.find_by_username(data['username'])
            #     if existing_user and existing_user.uid != data_db.uid:
            #         return jsonify({
            #             'status': 'error',
            #             'message': 'Username già esistente'
            #         }), 409
            #     data_db.username = data['username'].strip()
            
            # Aggiorna email se fornita e diversa
            if 'e_mail' in data and data['e_mail'] != data_db.e_mail:
                existing = User.find_by_email(data['e_mail'])
                if existing and existing.uid != data_db.uid:
                    return jsonify({
                        'status': 'error',
                        'message': 'Email già esistente'
                    }), 409
                data_db.email = data['e_mail'].strip()
            
            # # Aggiorna password se fornita
            # if 'password' in data and data['password']:
            #     if len(data['password']) < 8:
            #         return jsonify({
            #             'status': 'error',
            #             'message': 'Password deve essere di almeno 8 caratteri'
            #         }), 400
            #     data_db.set_password(data['password'])
            
            # if 'societa_di_riferimento' in data:
            #     data_db.societa_di_riferimento = data['societa_di_riferimento'].strip() if data['societa_di_riferimento'] else None
                
            # if 'company' in data:
            #     company_values = data['company']
            #     if isinstance(company_values, list) and company_values:
            #         company_uid = company_values[0]
            #         company = Company.query.filter_by(uid=company_uid).first()
            #         if not company:
            #             return jsonify({'status': 'error', 'message': 'Società non trovata'}), 404
            #         user.company = company
            #     else:
            #         user.company = None

            if 'societa_di_riferimento' in data:
                check_values = data['societa_di_riferimento']
                if isinstance(check_values, list) and check_values:
                    check_values_uid = check_values[0]
                    # response = Company.query.filter_by(uid=check_values_uid).first()
                    # print(f"TEST----------->{response}")
                    # if not response:
                    #     return jsonify({'status': 'error', 'message': 'Società non trovata'}), 404
                    data_db.societa_di_riferimento = check_values_uid
                else:
                    data_db.societa_di_riferimento = None

                # Non permettere di disattivare se stesso
                # if data_db.uid == g.current_user.uid and not data['is_active']:
                #     return jsonify({
                #         'status': 'error',
                #         'message': 'Non puoi disattivare te stesso'
                #     }), 400
                # data_db.is_active = bool(data['is_active'])

            # ==================== STATUS ACCOUNT ====================
            if 'is_active' in data:
                # Non permettere di disattivare se stesso
                # if data_db.uid == g.current_user.uid and not data['is_active']:
                #     return jsonify({
                #         'status': 'error',
                #         'message': 'Non puoi disattivare te stesso'
                #     }), 400
                data_db.is_active = bool(data['is_active']) if data['is_active'] else None
            else:
                data_db.is_active = False   

            
            if 'societa_principale' in data:
                # Non permettere di disattivare se stesso
                # if data_db.uid == g.current_user.uid and not data['is_active']:
                #     return jsonify({
                #         'status': 'error',
                #         'message': 'Non puoi disattivare te stesso'
                #     }), 400
                data_db.societa_principale = bool(data['societa_principale']) if data['societa_principale'] else None
            else:
                data_db.societa_principale = False   
          
            
            # Gestisco le società collegate
            if 'societa_collegate' in data:
                
                related_uids = data['societa_collegate']
                print(related_uids)
                data_db.related_companies.clear()
                if isinstance(related_uids, list):
                    if related_uids:
                        # Se ci sono uid, aggiorna le relazioni
                        related_companies = Company.query.filter(Company.uid.in_(related_uids)).all()
                        data_db.related_companies = related_companies
                    else:
                        print("sono qui")
                        # Lista vuota -> rimuove tutte le relazioni
                        data_db.related_companies.clear()
                else:
                    print("sono qui qui")
                    # Se non è una lista valida → svuota
                    data_db.related_companies.clear()

            # Gestisco l'avata
            if not data.get('base64_avatar') or data['base64_avatar'] in ['null', 'undefined']:
                data_db.profile_image = None
                
            else:
                base64_data = data['base64_avatar']
                if base64_data:
                    upload_folder = os.path.join(AVATAR_FOLDER)
                    os.makedirs(upload_folder, exist_ok=True)
                    print(upload_folder)
                    filename = 'img_'+data["uid"] + '.jpg'
                    filepath = os.path.join(upload_folder, filename)

                    if ',' in base64_data:
                        base64_data = base64_data.split(',')[1]

                    with open(filepath, 'wb') as f:
                        f.write(base64.b64decode(base64_data))
                    print(filename)
                    data_db.logo = filename
                else:
                    data_db.logo = None

            # if 'company' in data:
            #     company_values = data['company']
            #     if isinstance(company_values, list) and company_values:
            #         company_uid = company_values[0]
            #         company = Company.query.filter_by(uid=company_uid).first()
            #         if not company:
            #             return jsonify({'status': 'error', 'message': 'Società non trovata'}), 404
            #         data_db.company = company
            #     else:
            #         data_db.company = None


            # Salva le modifiche
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': 'Utente aggiornato con successo',
                'user': data_db.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Errore nell\'aggiornamento: {str(e)}'
            }), 500