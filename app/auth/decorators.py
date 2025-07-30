from functools import wraps
from flask import jsonify, flash, redirect, url_for, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User

# ==================== DECORATORI WEB ====================

def role_required(*roles):
    """Decorator per richiedere ruoli specifici nelle route web"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Controlla se l'utente è loggato
            if not g.user:
                flash({'status': 'error',
                    'response': 'login_richiesto', 
                    'title': 'Accesso richiesto!',
                    'message': 'Devi effettuare il login per accedere a questa pagina.'
                    })
                return redirect(url_for('auth.web_login'))
            
            # Controlla i ruoli
            if not g.user.has_any_role(roles):
                flash({'status': 'error',
                    'response': 'accesso_negato', 
                    'title': 'Accesso negato!',
                    'message': f'Non hai i permessi necessari. Ruoli richiesti: {", ".join(roles)}'
                    })
                return redirect(url_for('web.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator per richiedere ruolo admin nelle route web"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user:
            flash({'status': 'error',
                'response': 'login_richiesto', 
                'title': 'Accesso richiesto!',
                'message': 'Devi effettuare il login per accedere a questa pagina.'
                })
            return redirect(url_for('auth.web_login'))
        
        if not g.user.is_admin():
            flash({'status': 'error',
                'response': 'admin_richiesto', 
                'title': 'Accesso riservato agli admin!',
                'message': 'Solo gli amministratori possono accedere a questa sezione.'
                })
            return redirect(url_for('web.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def moderator_required(f):
    """Decorator per richiedere ruolo moderator o admin nelle route web"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user:
            flash({'status': 'error',
                'response': 'login_richiesto', 
                'title': 'Accesso richiesto!',
                'message': 'Devi effettuare il login per accedere a questa pagina.'
                })
            return redirect(url_for('auth.web_login'))
        
        if not g.user.can_manage_users():
            flash({'status': 'error',
                'response': 'moderator_richiesto', 
                'title': 'Accesso riservato ai moderatori!',
                'message': 'Solo i moderatori e amministratori possono accedere a questa sezione.'
                })
            return redirect(url_for('web.dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== DECORATORI API ====================

def api_role_required(*roles):
    """Decorator per richiedere ruoli specifici nelle route API"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_uid = get_jwt_identity()
            # user = User.query.get(current_user_uid)
            user = User.find_by_uid(current_user_uid) 

            if not user or not user.is_active or not user.is_email_confirmed:
                return jsonify({
                    'status': 'error',
                    'response': 'utente_non_autorizzato',
                    'title': 'Utente non autorizzato!',
                    'message': 'L\'utente non è valido o non è attivo.'
                }), 401
            
            if not user.has_any_role(roles):
                return jsonify({
                    'status': 'error',
                    'response': 'ruolo_insufficiente',
                    'title': 'Permessi insufficienti!',
                    'message': f'Ruoli richiesti: {", ".join(roles)}. I tuoi ruoli: {", ".join(user.get_role_names())}'
                }), 403
            
            # Rende l'utente disponibile nella route
            g.current_user = user
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def api_admin_required(f):
    """Decorator per richiedere ruolo admin nelle route API"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_uid = get_jwt_identity()
        # user = User.query.get(current_user_uid)
        user = User.find_by_uid(current_user_uid) 
        
        if not user or not user.is_active or not user.is_email_confirmed:
            return jsonify({
                'status': 'error',
                'response': 'utente_non_autorizzato',
                'title': 'Utente non autorizzato!',
                'message': 'L\'utente non è valido o non è attivo.'
            }), 401
        
        if not user.is_admin():
            return jsonify({
                'status': 'error',
                'response': 'admin_richiesto',
                'title': 'Accesso riservato agli admin!',
                'message': 'Solo gli amministratori possono accedere a questa risorsa.'
            }), 403
        
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def api_moderator_required(f):
    """Decorator per richiedere ruolo moderator o admin nelle route API"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_uid = get_jwt_identity()
        # user = User.query.get(current_user_uid)
        user = User.find_by_uid(current_user_uid) 
        
        if not user or not user.is_active or not user.is_email_confirmed:
            return jsonify({
                'status': 'error',
                'response': 'utente_non_autorizzato',
                'title': 'Utente non autorizzato!',
                'message': 'L\'utente non è valido o non è attivo.'
            }), 401
        
        if not user.can_manage_users():
            return jsonify({
                'status': 'error',
                'response': 'moderator_richiesto',
                'title': 'Accesso riservato ai moderatori!',
                'message': 'Solo i moderatori e amministratori possono accedere a questa risorsa.'
            }), 403
        
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function