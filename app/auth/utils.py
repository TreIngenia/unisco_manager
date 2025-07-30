from functools import wraps
from flask import session, redirect, url_for, g
from app.models.user import User
from app.auth.jwt_session import unified_login_required

login_required = unified_login_required

def login_required(f):
    """Decorator per richiedere login su route web"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_uid' not in session:
            return redirect(url_for('auth.web_login'))
        return f(*args, **kwargs)
    return decorated_function

def load_logged_in_user():
    """Carica l'utente loggato nella sessione"""
    user_uid = session.get('user_uid')
    
    if user_uid is None:
        g.user = None
    else:
        g.user = User.find_by_uid(user_uid)
        if g.user and not g.user.is_active:
            g.user = None
            session.clear()

def login_user(user):
    """Effettua il login dell'utente nella sessione"""
    from flask import session
    session.permanent = True
    session['user_uid'] = user.uid
    session['username'] = user.username

def logout_user():
    """Effettua il logout dell'utente"""
    session.clear()