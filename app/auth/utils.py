from functools import wraps
from flask import session, redirect, url_for, g
from app.models.user import User

def login_required(f):
    """Decorator per richiedere login su route web"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.web_login'))
        return f(*args, **kwargs)
    return decorated_function

def load_logged_in_user():
    """Carica l'utente loggato nella sessione"""
    user_id = session.get('user_id')
    
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)
        if g.user and not g.user.is_active:
            g.user = None
            session.clear()

def login_user(user):
    """Effettua il login dell'utente nella sessione"""
    session['user_id'] = user.id
    session['username'] = user.username

def logout_user():
    """Effettua il logout dell'utente"""
    session.clear()