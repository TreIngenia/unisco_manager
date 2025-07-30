from flask import render_template, redirect, url_for, g, flash, request, jsonify
from app.auth.utils import login_required
from app.models.user import User
from flask_login import current_user
from app import db

def register_web_routes(web_bp):
    
    @web_bp.route('/', endpoint="home")
    def home():
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
            username = request.form.get('email')
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
    
    # Aggiungi anche questa route per la pagina profilo utente normale
    @web_bp.route('/profile/data', methods=['GET', 'POST'])
    @login_required
    def profile_data():
        """Gestione dati profilo utente"""
        if request.method == 'POST':
            data = request.get_json() if request.is_json else request.form
            
            # Aggiorna solo i campi che l'utente può modificare
            try:
                if 'username' in data and data['username'] != g.user.username:
                    existing_user = User.find_by_username(data['username'])
                    if existing_user:
                        if request.is_json:
                            return jsonify({
                                'status': 'error',
                                'message': 'Username già esistente'
                            }), 409
                        else:
                            flash('Username già esistente', 'error')
                            return redirect(url_for('web.profile_data'))
                    
                    g.user.username = data['username']
                
                if 'email' in data and data['email'] != g.user.email:
                    existing_user = User.find_by_email(data['email'])
                    if existing_user:
                        if request.is_json:
                            return jsonify({
                                'status': 'error',
                                'message': 'Email già esistente'
                            }), 409
                        else:
                            flash('Email già esistente', 'error')
                            return redirect(url_for('web.profile_data'))
                    
                    g.user.email = data['email']
                    g.user.is_email_confirmed = False  # Richiede nuova conferma

                first_name = data['first_name']
                last_name = data['last_name']
                phone = data['phone']
                g.user.first_name = first_name
                g.user.last_name = last_name
                g.user.phone = phone

                db.session.commit()
                
                if request.is_json:
                    return jsonify({
                        'status': 'success',
                        'message': 'Profilo aggiornato con successo',
                        'user': g.user.to_dict(include_roles=True)
                    })
                else:
                    flash('Profilo aggiornato con successo', 'success')
                    return redirect(url_for('web.profile'))
                    
            except Exception as e:
                db.session.rollback()
                if request.is_json:
                    return jsonify({
                        'status': 'error',
                        'message': f'Errore nell\'aggiornamento: {str(e)}'
                    }), 500
                else:
                    flash('Errore nell\'aggiornamento profilo', 'error')
                    return redirect(url_for('web.profile_data'))
        
        # GET - Mostra form o restituisce dati
        if request.is_json:
            return jsonify(g.user.to_dict(include_roles=True))
        else:
            return render_template('web/profile_data.html', user=g.user)

    @web_bp.route('/profile/password', methods=['GET', 'POST'])
    @login_required
    def change_user_password():
        """Cambio password utente"""
        if request.method == 'POST':
            data = request.get_json() if request.is_json else request.form
            
            current_password = data.get('actual_password')
            new_password = data.get('password')
            confirm_password = data.get('confirm_password')
            
            # Validazione
            if not current_password or not new_password or not confirm_password:
                error_msg = 'Tutti i campi sono obbligatori'
                if request.is_json:
                    return jsonify({'status': 'error', 'message': error_msg}), 400
                else:
                    flash(error_msg, 'error')
                    return redirect(url_for('web.change_user_password'))
            
            if not g.user.check_password(current_password):
                error_msg = 'Password attuale non corretta'
                if request.is_json:
                    return jsonify({'status': 'error', 'message': error_msg}), 400
                else:
                    flash(error_msg, 'error')
                    return redirect(url_for('web.change_user_password'))
            
            if new_password != confirm_password:
                error_msg = 'Le nuove password non coincidono'
                if request.is_json:
                    return jsonify({'status': 'error', 'message': error_msg}), 400
                else:
                    flash(error_msg, 'error')
                    return redirect(url_for('web.change_user_password'))
            
            if len(new_password) < 8:
                error_msg = 'La password deve essere di almeno 8 caratteri'
                if request.is_json:
                    return jsonify({'status': 'error', 'message': error_msg}), 400
                else:
                    flash(error_msg, 'error')
                    return redirect(url_for('web.change_user_password'))
            
            try:
                g.user.set_password(new_password)
                db.session.commit()
                
                success_msg = 'Password cambiata con successo'
                if request.is_json:
                    return jsonify({'status': 'success', 'message': success_msg})
                else:
                    flash(success_msg, 'success')
                    return redirect(url_for('web.profile'))
                    
            except Exception as e:
                db.session.rollback()
                error_msg = 'Errore nel cambio password'
                if request.is_json:
                    return jsonify({'status': 'error', 'message': error_msg}), 500
                else:
                    flash(error_msg, 'error')
                    return redirect(url_for('web.change_user_password'))
        
        # GET - Mostra form
        return render_template('web/change_password.html')    

    @web_bp.route('/api/resend-confirmation', methods=['POST'])
    @login_required
    def resend_confirmation():
        """Invia nuovamente email di conferma"""
        if g.user.is_email_confirmed:
            return jsonify({
                'status': 'error',
                'message': 'Email già confermata'
            }), 400
        
        try:
            # Genera nuovo token di conferma
            from secrets import token_urlsafe
            from datetime import datetime, timedelta
            
            g.user.email_confirmation_token = token_urlsafe(32)
            g.user.email_confirmation_sent_at = datetime.utcnow()
            
            db.session.commit()
            
            # Qui dovresti inviare l'email di conferma
            # send_confirmation_email(g.user)
            
            return jsonify({
                'status': 'success',
                'message': 'Email di conferma inviata con successo'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'status': 'error',
                'message': f'Errore nell\'invio email: {str(e)}'
            }), 500

    @web_bp.route('/api/export-user-data', methods=['POST'])
    @login_required
    def export_user_data():
        """Esporta dati utente in formato JSON"""
        try:
            user_data = {
                'account_info': {
                    'id': g.user.uid,
                    'username': g.user.username,
                    'email': g.user.email,
                    'is_active': g.user.is_active,
                    'is_email_confirmed': g.user.is_email_confirmed,
                    'created_at': g.user.created_at.isoformat() if g.user.created_at else None,
                    'last_login': g.user.last_login.isoformat() if g.user.last_login else None
                },
                'roles': [role.name for role in g.user.roles],
                'export_date': datetime.utcnow().isoformat(),
                'export_format': 'JSON'
            }
            
            from flask import make_response
            import json
            
            response = make_response(json.dumps(user_data, indent=2))
            response.headers['Content-Type'] = 'application/json'
            response.headers['Content-Disposition'] = 'attachment; filename=i_miei_dati.json'
            
            return response
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Errore nell\'esportazione: {str(e)}'
            }), 500

    @web_bp.route('/confirm-email/<token>')
    def confirm_email(token):
        """Conferma email tramite token"""
        user = User.query.filter_by(email_confirmation_token=token).first()
        
        if not user:
            flash('Token di conferma non valido', 'error')
            return redirect(url_for('web.profile'))
        
        # Verifica scadenza token (24 ore)
        if user.email_confirmation_sent_at:
            from datetime import datetime, timedelta
            if datetime.utcnow() - user.email_confirmation_sent_at > timedelta(hours=24):
                flash('Token di conferma scaduto', 'error')
                return redirect(url_for('web.profile'))
        
        try:
            user.is_email_confirmed = True
            user.email_confirmation_token = None
            user.email_confirmation_sent_at = None
            
            db.session.commit()
            
            flash('Email confermata con successo!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash('Errore nella conferma email', 'error')
        
        return redirect(url_for('web.profile'))
    