from flask import render_template, redirect, url_for, g, flash, request
from app.auth.utils import login_required
from app.models.user import User
from flask_login import current_user

def register_web_routes(web_bp):
    
    @web_bp.route('/')
    def index():
        # return render_template('web/index.html')
        if g.user:
            return redirect(url_for('web.dashboard'))
        return redirect(url_for('auth.web_login'))
    

    @web_bp.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('web/dashboard.html', user=g.user)

    @web_bp.route('/profile')
    @login_required
    def profile():
        return render_template('web/profile.html', user=g.user)

    @web_bp.route('/profile/edit', methods=['GET', 'POST'])
    @login_required
    def edit_profile():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            
            if username and username != g.user.username:
                # Controllo case-insensitive per username
                if User.find_by_username(username):
                    flash('Username già esistente')
                    return render_template('web/edit_profile.html', user=g.user)
                g.user.username = username
            
            if email and email != g.user.email:
                # Controllo case-insensitive per email
                if User.find_by_email(email):
                    flash('Email già esistente')
                    return render_template('web/edit_profile.html', user=g.user)
                g.user.email = email
            
            from app import db
            db.session.commit()
            flash('Profilo aggiornato con successo')
            return redirect(url_for('web.profile'))
        
        return render_template('web/edit_profile.html', user=g.user)

    @web_bp.route('/settings', methods=['GET', 'POST'])
    @login_required
    def settings():
        if request.method == 'POST':
            # Qui puoi gestire le preferenze utente
            flash('Preferenze salvate con successo')
            return redirect(url_for('web.settings'))
        
        return render_template('web/settings.html')

    @web_bp.route('/stats')
    @login_required
    def stats():
        # Qui puoi calcolare le statistiche dell'utente
        from datetime import datetime
        account_age = (datetime.utcnow() - g.user.created_at).days
        
        stats_data = {
            'last_login': g.user.created_at,  # Placeholder
            'total_logins': 1,  # Placeholder
            'account_age': f"{account_age} giorni"
        }
        
        return render_template('web/stats.html', user=g.user, **stats_data)

    @web_bp.route('/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        if request.method == 'POST':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_new_password')
            
            if not g.user.check_password(current_password):
                flash('Password attuale non corretta')
                return render_template('web/change_password.html')
            
            if new_password != confirm_password:
                flash('Le password non coincidono')
                return render_template('web/change_password.html')
            
            if len(new_password) < 8:
                flash('La password deve essere di almeno 8 caratteri')
                return render_template('web/change_password.html')
            
            g.user.set_password(new_password)
            from app import db
            db.session.commit()
            flash('Password cambiata con successo')
            return redirect(url_for('web.profile'))
        
        return render_template('web/change_password.html')

    @web_bp.route('/logout')
    def logout():
        return redirect(url_for('auth.web_logout'))