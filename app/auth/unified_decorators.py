from functools import wraps
from flask import session, request, jsonify, redirect, url_for, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User

def unified_api_login_required(f):
    """Decorator per API che supporta sia JWT cookies che sessioni"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = None
        
        # Prima prova JWT cookie
        try:
            verify_jwt_in_request(optional=True)
            user_uid_str = get_jwt_identity()
            if user_uid_str:
                # user_uid = int(user_uid_str)
                # user = User.query.filter_by(uid=user_uid).first()
                user = User.find_by_uid(user_uid_str) 
                if user and user.is_active and user.is_email_confirmed:
                    g.current_user = user
                    return f(*args, **kwargs)
        except Exception:
            pass
        
        # Fallback su sessione Flask
        user_uid = session.get('user_uid')
        if user_uid:
            # user = User.query.filter_by(uid=user_uid).first()
            user = User.find_by_uid(user_uid) 
            if user and user.is_active and user.is_email_confirmed:
                g.current_user = user
                return f(*args, **kwargs)
        
        # Nessuna autenticazione valida
        return jsonify({
            'status': 'error',
            'response': 'login_richiesto',
            'title': 'Accesso richiesto!',
            'message': 'Devi effettuare il login per accedere a questa risorsa.'
        }), 401
    
    return decorated_function

def unified_api_admin_required(f):
    """Decorator per API che richiede admin (JWT cookies + sessioni)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = None
        
        # Prima prova JWT cookie
        try:
            verify_jwt_in_request(optional=True)
            user_uid_str = get_jwt_identity()
            if user_uid_str:
                # user_uid = int(user_uid_str)
                # user = User.query.filter_by(uid=user_uid).first()
                user = User.find_by_uid(user_uid_str) 
                if user and user.is_active and user.is_email_confirmed and user.is_admin():
                    g.current_user = user
                    return f(*args, **kwargs)
        except Exception:
            pass
        
        # Fallback su sessione Flask
        user_uid = session.get('user_uid')
        if user_uid:
            # user = User.query.filter_by(uid=user_uid).first()
            user = User.find_by_uid(user_uid) 
            if user and user.is_active and user.is_email_confirmed and user.is_admin():
                g.current_user = user
                return f(*args, **kwargs)
        
        # Controllo permessi
        if user and user.is_active and user.is_email_confirmed:
            if not user.is_admin():
                return jsonify({
                    'status': 'error',
                    'response': 'admin_richiesto',
                    'title': 'Accesso riservato agli admin!',
                    'message': 'Solo gli amministratori possono accedere a questa risorsa.'
                }), 403
        
        # Nessuna autenticazione valida
        return jsonify({
            'status': 'error',
            'response': 'login_richiesto',
            'title': 'Accesso richiesto!',
            'message': 'Devi effettuare il login per accedere a questa risorsa.'
        }), 401
    
    return decorated_function

def unified_api_moderator_required(f):
    """Decorator per API che richiede moderator o admin (JWT cookies + sessioni)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = None
        
        # Prima prova JWT cookie
        try:
            verify_jwt_in_request(optional=True)
            user_uid_str = get_jwt_identity()
            if user_uid_str:
                # user_uid = int(user_uid_str)
                # user = User.query.filter_by(uid=user_uid).first()
                user = User.find_by_uid(user_uid_str) 
                if user and user.is_active and user.is_email_confirmed and user.can_manage_users():
                    g.current_user = user
                    return f(*args, **kwargs)
        except Exception:
            pass
        
        # Fallback su sessione Flask
        user_uid = session.get('user_uid')
        if user_uid:
            user = User.query.filter_by(uid=user_uid).first()
            if user and user.is_active and user.is_email_confirmed and user.can_manage_users():
                g.current_user = user
                return f(*args, **kwargs)
        
        # Controllo permessi
        if user and user.is_active and user.is_email_confirmed:
            if not user.can_manage_users():
                return jsonify({
                    'status': 'error',
                    'response': 'moderator_richiesto',
                    'title': 'Accesso riservato ai moderatori!',
                    'message': 'Solo i moderatori e amministratori possono accedere a questa risorsa.'
                }), 403
        
        # Nessuna autenticazione valida
        return jsonify({
            'status': 'error',
            'response': 'login_richiesto',
            'title': 'Accesso richiesto!',
            'message': 'Devi effettuare il login per accedere a questa risorsa.'
        }), 401
    
    return decorated_function