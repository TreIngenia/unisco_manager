from flask import request, jsonify, render_template, redirect, url_for, flash, session, make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from app.auth.utils import login_user, logout_user
from app.services.email import EmailService
from app import db
from app.auth.jwt_session import unified_login_user, unified_logout_user
from flask_jwt_extended import set_access_cookies, unset_jwt_cookies
from datetime import datetime, timedelta

def register_auth_routes(auth_bp):
    
    # Route API per login
    @auth_bp.route('/api/login', methods=['POST'])
    def api_login():
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Email e password richiesti'}), 400
        
        # Ricerca per username (che corrisponde all'email)
        user = User.find_by_username(data['username'])
        
        if user and user.check_password(data['password']) and user.is_active:
            # Controlla se l'email è confermata
            if not user.is_email_confirmed:
                return jsonify({
                    'status': 'error',
                    'response': 'email_non_confermata',
                    'title': 'Email non confermata!',
                    'message': 'Devi confermare la tua email prima di accedere. Controlla la tua casella di posta.'
                }), 403
            
            access_token = create_access_token(identity=user.uid)
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict()
            })
        
        return jsonify({'status': 'error',
                        'response': 'errore_credenziali', 
                        'title': 'Credenziali non valide!',
                        'message': 'La username o la password inserite non sono valide, riprova.'
                        }), 401


    # Route API per registrazione
    @auth_bp.route('/api/register', methods=['POST'])
    def api_register():
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email e password richiesti'}), 400
        
        # Controllo esistenza email (salvata come username)
        if User.find_by_username(data['email']):
            return jsonify({'error': 'Email già registrata'}), 409
        
        # Salva l'email sia come username che come email
        user = User(
            username=data['email'],  # Email salvata come username
            email=data['email'],     # Email salvata anche come email
            is_active=True,
            is_email_confirmed=False  # Email non confermata inizialmente
        )
        user.set_password(data['password'])
        
        # Genera token di conferma
        confirmation_token = user.generate_confirmation_token()
        
        db.session.add(user)
        db.session.commit()
        # db.session.flush()

        # from app.models.role import Role
        # default_role = Role.get_default_role()
        # print(f"Ruolo---------------->{default_role}")
        # if default_role:
        #     user.add_role(default_role)
        #     db.session.commit()
            

        # Invia email di conferma
        EmailService.send_confirmation_email(
            user.email, 
            user.username, 
            confirmation_token
        )
        
        return jsonify({
            'message': 'Utente registrato con successo',
            'status': 'success',
            'response': 'utente_registrato',
            'title': 'Registrazione completata!',
            'message': 'Controlla la tua email per confermare la registrazione.',
            'user': user.to_dict()
        }), 201


    # Route per verifica token
    @auth_bp.route('/api/verify', methods=['GET'])
    @jwt_required()
    def verify_token():
        current_user_uid = get_jwt_identity()
        user = User.query.get(current_user_uid)
        
        if user and user.is_active and user.is_email_confirmed:
            return jsonify({'valid': True, 'user': user.to_dict()})
        
        return jsonify({'valid': False}), 401
    

    

    @auth_bp.route('/login', methods=['GET', 'POST'])
    def web_login():
        if request.method == 'GET':
            return render_template('auth/login.html')
        
        # POST - Elabora il login
        user_input = request.form.get('username')
        password = request.form.get('password')
        
        if not user_input or not password:
            return render_template('auth/login.html', 
                                   msg={'status': 'error',
                                    'response': 'credenziali_richieste', 
                                    'title': 'Credenziali richieste!',
                                    'message': 'La username o la password devono essere obbligatoriamente inserite. Riprova.'
                                    })
        
        # Ricerca per username (che corrisponde all'email)
        user = User.find_by_username(user_input)
        
        if user and user.check_password(password) and user.is_active:
            # Controlla se l'email è confermata
            if not user.is_email_confirmed:
                return render_template('auth/login.html',
                                        msg={'status': 'warning',
                                            'response': 'email_non_confermata', 
                                            'title': 'Email non confermata!',
                                            'message': 'Devi confermare la tua email prima di accedere. Controlla la tua casella di posta.',
                                            'action_url': url_for('auth.resend_confirmation', email=user.email),
                                            'action_text': 'Reinvia email di conferma'
                                        })
            
            # === LOGIN RIUSCITO CON JWT + SESSIONE ===
            
            # Sistema esistente (manteniamo per compatibilità)
            login_user(user)
            
            # NUOVO: Crea JWT token
            # access_token = create_access_token(identity=user.id)
            access_token = create_access_token(identity=str(user.uid))
            
            # Aggiorna last_login
            user.last_login = datetime.utcnow() 
            db.session.commit()
            
            flash('Login effettuato con successo')
            
            # Redirect con JWT cookie sicuro
            next_page = request.args.get('next')
            response = redirect(next_page) if next_page else redirect(url_for('web.dashboard'))
            
            # CRITICO: Imposta JWT come httpOnly cookie
            set_access_cookies(response, access_token)
            
            return response
        
        # === LOGIN FALLITO ===
        return render_template('auth/login.html', 
                                msg={'status': 'error',
                                    'response': 'credenziali_errate', 
                                    'title': 'Credenziali non valide!',
                                    'message': 'La username o la password inserite non sono valide. Riprova.'
                                })
        
        # === LOGIN FALLITO ===
        return render_template('auth/login.html', 
                                msg={'status': 'error',
                                    'response': 'credenziali_errate', 
                                    'title': 'Credenziali non valide!',
                                    'message': 'La username o la password inserite non sono valide. Riprova.'
                                })


    # Route WEB per registrazione
    @auth_bp.route('/register', methods=['GET', 'POST'])
    def web_register():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not email or not password:
                # flash('Email e password richiesti')
                return render_template('auth/register.html', msg={'status': 'error',
                        'response': 'credenziali_richieste', 
                        'title': 'Credenziali richieste!',
                        'message': 'L\'indirizzo mail e la password sono obbligatorie.'
                        })
            
            # Controllo esistenza email (salvata come username)
            check_user = User.find_by_username(email)
            if check_user:
                if not check_user.is_email_confirmed:
                    return render_template('auth/register.html',
                                           msg={'status': 'warning',
                                            'response': 'email_non_confermata', 
                                            'title': 'Email non confermata!',
                                            'message': 'Il tuo indirizzo E-Mail risulta inserito ma non ancora confermato. <br> Devi confermare la tua email prima di accedere. Controlla la tua casella di posta.',
                                            'action_url': url_for('auth.resend_confirmation', email=check_user.email),
                                            'action_text': 'Reinvia email di conferma'
                                            })
                
                return render_template('auth/register.html', msg={'status': 'error',
                        'response': 'utente_esistente', 
                        'title': 'Utente già registrato!',
                        'message': 'Esiste già un utente con questo indirizzo e-mail, usane uno differente.'
                        })
            
            # Salva l'email sia come username che come email
            user = User(
                username=email,  # Email salvata come username
                email=email,     # Email salvata anche come email
                is_active=True,
                is_email_confirmed=False  # Email non confermata inizialmente
            )
            user.set_password(password)
            
            # Genera token di conferma
            confirmation_token = user.generate_confirmation_token()
            
            db.session.add(user)
            db.session.commit()
            db.session.flush()

            from app.models.role import Role
            default_role = Role.get_default_role()
            print(f"Ruolo---------------->{default_role}")
            if default_role:
                user.add_role(default_role)
                db.session.commit()
                
            # Invia email di conferma
            EmailService.send_confirmation_email(
                user.email, 
                user.username, 
                confirmation_token
            )
            
            return render_template('auth/email_sent.html', 
                                   msg={'status': 'success',
                                    'response': 'utente_registrato', 
                                    'title': 'Registrazione completata!',
                                    'message': 'Controlla la tua email per confermare la registrazione.'
                                    },
                                    email=user.email)
        
        return render_template('auth/register.html')

    # Route per conferma email
    @auth_bp.route('/confirm-email/<token>')
    def confirm_email(token):
        user = User.find_by_confirmation_token(token)
        
        if not user:
            return render_template('auth/email_confirmation_error.html',
                                    msg={'status': 'error',
                                        'response': 'token_invalido', 
                                        'title': 'Link non valido!',
                                        'message': 'Il link di conferma non è valido.',
                                        })
        
        if user.confirm_email(token):
            db.session.commit()
            return render_template('auth/email_confirmed.html', 
                                   msg={'status': 'success',
                                    'response': 'email_confermata', 
                                    'title': 'Email confermata!',
                                    'message': 'La tua email è stata confermata con successo. Ora puoi accedere.'
                                    },
                                    user=user)
        else:
            return render_template('auth/email_confirmation_error.html',
                                   msg={'status': 'error',
                                    'response': 'token_scaduto', 
                                    'title': 'Link scaduto!',
                                    'message': 'Il link di conferma è scaduto. Richiedi un nuovo link di conferma.',
                                    'action_url': url_for('auth.resend_confirmation', email=user.email),
                                    'action_text': 'Reinvia email di conferma'
                                    })

    # Route per reinviare email di conferma
    @auth_bp.route('/resend-confirmation')
    def resend_confirmation():
        email = request.args.get('email')
        if not email:
            return render_template('auth/email_confirmation_error.html',msg={'status': 'error',
                'response': 'email_mancante', 
                'title': 'Email mancante!',
                'message': 'Impossibile reinviare la conferma senza indirizzo email.'
                })
        
        user = User.find_by_username(email)
        if not user:
            return render_template('auth/email_confirmation_error.html', msg={'status': 'error',
                'response': 'utente_non_trovato', 
                'title': 'Utente non trovato!',
                'message': 'Nessun utente trovato con questo indirizzo email.'
                })
        
        if user.is_email_confirmed:
            return render_template('auth/email_confirmation_error.html', msg={'status': 'info',
                'response': 'email_gia_confermata', 
                'title': 'Email già confermata!',
                'message': 'La tua email è già stata confermata. Puoi accedere.'
                })
        
        # Genera nuovo token e reinvia email
        confirmation_token = user.generate_confirmation_token()
        db.session.commit()
        
        EmailService.send_confirmation_email(
            user.email, 
            user.username, 
            confirmation_token
        )
        
        return render_template('auth/email_sent.html', msg={'status': 'success',
            'response': 'email_reinviata', 
            'title': 'Email reinviata!',
            'message': 'Ti abbiamo inviato una nuova email di conferma. Controlla la tua casella di posta.'
            },email=user.email)

    
    # ################################# #
    # Route WEB per logout              # 
    # ################################# #
    @auth_bp.route('/logout')
    def web_logout():
        """Logout migliorato con pulizia cache"""
        from app.auth.utils import logout_user
        from flask_jwt_extended import unset_jwt_cookies
        
        logout_user()  # Rimuove la sessione
        
        # Crea response che rimuove anche il JWT cookie
        response = make_response(redirect(url_for('auth.web_login')))
        unset_jwt_cookies(response)
        
        # Aggiungi header per prevenire cache
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        flash('Logout effettuato con successo')
        return response
    
    # ################################# #
    # Route controllo autenticazione    # 
    # ################################# #
    @auth_bp.route('/api/check', methods=['GET'])
    def check_auth():
        """Endpoint per controllare lo stato di autenticazione"""
        # Prima prova JWT cookie
        try:
            from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
            verify_jwt_in_request(optional=True)
            user_uid = get_jwt_identity()
            if user_uid:
                user = User.find_by_uid(user_uid)
                if user and user.is_active:
                    return jsonify({'authenticated': True, 'user': user.to_dict()})
        except:
            pass
        
        # Fallback su sessione
        user_uid = session.get('user_uid')
        if user_uid:
            user = User.find_by_uid(user_uid)
            if user and user.is_active:
                return jsonify({'authenticated': True, 'user': user.to_dict()})
        
        return jsonify({'authenticated': False}), 401
    
    # ################################# #
    # Route per il reset della password # 
    # ################################# #

    # Route per richiesta reset password
    @auth_bp.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        if request.method == 'POST':
            email = request.form.get('email')
            
            if not email:
                return render_template('auth/forgot_password.html', msg={'status': 'error',
                    'response': 'email_richiesta', 
                    'title': 'Email richiesta!',
                    'message': 'Inserisci il tuo indirizzo email per procedere.'
                    })
            
            user = User.find_by_username(email)
            
            if user and user.is_active:
                # Genera token di reset password
                reset_token = user.generate_password_reset_token()
                db.session.commit()
                
                # Invia email di reset
                EmailService.send_password_reset_email(
                    user.email, 
                    user.username, 
                    reset_token
                )
                
                return render_template('auth/password_reset_sent.html', msg={'status': 'success',
                    'response': 'email_reset_inviata', 
                    'title': 'Email inviata!',
                    'message': 'Ti abbiamo inviato un link per reimpostare la password. Controlla la tua email.'
                    }, email=user.email)
            else:
                # Per sicurezza, non rivelare se l'email esiste o no
                return render_template('auth/password_reset_sent.html', msg={'status': 'success',
                    'response': 'email_reset_inviata', 
                    'title': 'Email inviata!',
                    'message': 'Se l\'email esiste nel nostro sistema, riceverai un link per il reset.'
                    }, email=email)
        
        return render_template('auth/forgot_password.html')

    # Route per reset password con token
    @auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
    def reset_password(token):
        user = User.find_by_password_reset_token(token)
        
        if not user:
         
            return render_template('auth/password_reset_error.html', msg={'status': 'error',
                'response': 'token_invalido', 
                'title': 'Link non valido!',
                'message': 'Il link di reset password non è valido o è scaduto.'
                })
        
        if not user.is_password_reset_token_valid(token):
           
            return render_template('auth/password_reset_error.html', msg={'status': 'error',
                'response': 'token_scaduto', 
                'title': 'Link scaduto!',
                'message': 'Il link di reset password è scaduto. Richiedi un nuovo reset.'
                })
        
        if request.method == 'POST':
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if not new_password or not confirm_password:
              
                return render_template('auth/reset_password.html', msg={'status': 'error',
                    'response': 'password_richiesta', 
                    'title': 'Password richiesta!',
                    'message': 'Inserisci la nuova password e la conferma.'
                    }, token=token)
            
            if new_password != confirm_password:
                
                return render_template('auth/reset_password.html', msg={'status': 'error',
                    'response': 'password_non_coincidono', 
                    'title': 'Password diverse!',
                    'message': 'Le password inserite non coincidono. Riprova.'
                    },token=token)
            
            if len(new_password) < 8:
                
                return render_template('auth/reset_password.html', msg={'status': 'error',
                    'response': 'password_troppo_corta', 
                    'title': 'Password troppo corta!',
                    'message': 'La password deve essere di almeno 8 caratteri.'
                    }, token=token)
            
            # Reset password
            if user.reset_password(token, new_password):
                db.session.commit()
                
                return render_template('auth/password_reset_success.html', msg={'status': 'success',
                    'response': 'password_resettata', 
                    'title': 'Password aggiornata!',
                    'message': 'La tua password è stata aggiornata con successo. Ora puoi accedere.'
                    }, user=user)
            else:
                
                return render_template('auth/password_reset_error.html', msg={'status': 'error',
                    'response': 'errore_reset', 
                    'title': 'Errore reset!',
                    'message': 'Si è verificato un errore durante il reset. Riprova.'
                    })
        
        return render_template('auth/reset_password.html', token=token)
    
    @auth_bp.route('/debug/jwt-config')
    def debug_jwt_config():
        """Mostra le configurazioni JWT"""
        from flask import current_app
        
        jwt_config = {
            'JWT_TOKEN_LOCATION': current_app.config.get('JWT_TOKEN_LOCATION'),
            'JWT_COOKIE_SECURE': current_app.config.get('JWT_COOKIE_SECURE'),
            'JWT_COOKIE_CSRF_PROTECT': current_app.config.get('JWT_COOKIE_CSRF_PROTECT'),
            'JWT_ACCESS_COOKIE_NAME': current_app.config.get('JWT_ACCESS_COOKIE_NAME'),
            'JWT_COOKIE_SAMESITE': current_app.config.get('JWT_COOKIE_SAMESITE'),
        }
        
        return jsonify(jwt_config)

    @auth_bp.route('/debug/cookies')
    def debug_cookies():
        """Mostra tutti i cookies ricevuti"""
        return jsonify({
            'cookies': dict(request.cookies),
            'headers': dict(request.headers),
            'has_jwt_cookie': 'access_token_cookie' in request.cookies,
            'cookie_names': list(request.cookies.keys())
        })

    @auth_bp.route('/debug/test-jwt')
    def debug_test_jwt():
        """Test JWT dal cookie"""
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'cookies': dict(request.cookies),
            'jwt_status': 'unknown'
        }
        
        try:
            verify_jwt_in_request(optional=True)
            user_uid = get_jwt_identity()
            result['jwt_status'] = 'valid' if user_uid else 'no_token'
            result['jwt_user_uid'] = user_uid
            
            if user_uid:
                user = User.query.get(user_uid)
                result['user_info'] = user.username if user else 'User not found'
                
        except Exception as e:
            result['jwt_status'] = f'error: {str(e)}'
        
        return jsonify(result)

    @auth_bp.route('/debug/session-config')
    def debug_session_config():
        """Mostra le configurazioni delle sessioni"""
        from flask import current_app
        
        session_config = {
            'PERMANENT_SESSION_LIFETIME': str(current_app.config.get('PERMANENT_SESSION_LIFETIME')),
            'SESSION_COOKIE_SECURE': current_app.config.get('SESSION_COOKIE_SECURE'),
            'SESSION_COOKIE_HTTPONLY': current_app.config.get('SESSION_COOKIE_HTTPONLY'),
            'SESSION_COOKIE_SAMESITE': current_app.config.get('SESSION_COOKIE_SAMESITE'),
        }
        
        return jsonify(session_config)

