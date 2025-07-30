from functools import wraps
from flask import session, request, jsonify, redirect, url_for, g
from flask_jwt_extended import (
    create_access_token, 
    set_access_cookies, 
    unset_jwt_cookies,
    verify_jwt_in_request,
    get_jwt_identity
)
from app.models.user import User

def unified_login_required(f):
    """Decorator che supporta sia sessioni che JWT cookies"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Prima prova JWT cookie
        try:
            verify_jwt_in_request(optional=True)
            user_uid = get_jwt_identity()
            if user_uid:
                # USA find_by_uid invece di query.get
                user = User.find_by_uid(user_uid)  # ← CAMBIATO
                if user and user.is_active:
                    g.user = user
                    return f(*args, **kwargs)
        except Exception:
            pass
        
        # Fallback su sessione esistente
        user_uid = session.get('user_uid')
        if user_uid:
            # USA find_by_uid invece di query.get
            user = User.find_by_uid(user_uid)  # ← CAMBIATO
            if user and user.is_active:
                g.user = user
                return f(*args, **kwargs)
        
        # Nessuna autenticazione valida
        return redirect(url_for('auth.web_login'))
    
    return decorated_function

# def unified_login_required(f):
#     """Decorator che supporta sia sessioni che JWT cookies"""
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         # Prima prova JWT cookie
#         try:
#             verify_jwt_in_request(optional=True)
#             user_uid = get_jwt_identity()
#             if user_uid:
#                 user = User.query.get(user_uid)
#                 if user and user.is_active:
#                     g.user = user
#                     return f(*args, **kwargs)
#         except Exception:
#             pass
        
#         # Fallback su sessione esistente
#         user_uid = session.get('user_uid')
#         if user_uid:
#             user = User.query.get(user_uid)
#             if user and user.is_active:
#                 g.user = user
#                 return f(*args, **kwargs)
        
#         # Nessuna autenticazione valida
#         return redirect(url_for('auth.web_login'))
    
#     return decorated_function

def unified_login_user(user, remember=False):
    """Login unificato che setta sia JWT cookie che sessione"""
    # Crea JWT access token - USA UID invece di ID
    access_token = create_access_token(identity=user.uid)  # ← CAMBIATO
    
    # Mantieni anche la sessione per compatibilità
    session['user_uid'] = user.uid  # ← CAMBIATO (era user.id)
    session['username'] = user.username
    
    return access_token
# def unified_login_user(user, remember=False):
#     """Login unificato che setta sia JWT cookie che sessione"""
#     # Crea JWT access token
#     access_token = create_access_token(identity=user.id)
    
#     # Mantieni anche la sessione per compatibilità
#     session['user_uid'] = user.id
#     session['username'] = user.username
    
#     return access_token

def unified_logout_user():
    """Logout unificato che rimuove sia JWT cookie che sessione"""
    session.clear()
    # I cookies JWT verranno rimossi nella response

def load_unified_user():
    """Carica l'utente da JWT cookie o sessione"""
    # Prima prova JWT cookie
    try:
        verify_jwt_in_request(optional=True)
        user_uid = get_jwt_identity()
        if user_uid:
            # USA find_by_uid invece di query.get
            user = User.find_by_uid(user_uid)  # ← CAMBIATO
            if user and user.is_active:
                g.user = user
                return
    except Exception:
        pass
    
    # Fallback su sessione esistente
    user_uid = session.get('user_uid')
    if user_uid:
        # USA find_by_uid invece di query.get
        user = User.find_by_uid(user_uid)  # ← CAMBIATO
        if user and user.is_active:
            g.user = user
        else:
            g.user = None
            session.clear()
    else:
        g.user = None

# def load_unified_user():
#     """Carica l'utente da JWT cookie o sessione"""
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
#         if user and user.is_active:
#             g.user = user
#         else:
#             g.user = None
#             session.clear()
#     else:
#         g.user = None