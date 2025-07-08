from flask import request, jsonify, render_template, redirect, url_for, flash, session
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models.user import User
from app.auth.utils import login_user, logout_user
from app.services.email import EmailService
from app import db

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
            
            access_token = create_access_token(identity=user.id)
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
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if user and user.is_active and user.is_email_confirmed:
            return jsonify({'valid': True, 'user': user.to_dict()})
        
        return jsonify({'valid': False}), 401
    

    # Route WEB per login
    @auth_bp.route('/login', methods=['GET', 'POST'])
    def web_login():
        if request.method == 'POST':
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
                
                login_user(user)
                flash('Login effettuato con successo')
                access_token = create_access_token(identity=str(user.id))
                # Redirect alla pagina richiesta o dashboard
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('web.dashboard', access_token=access_token))
            
            return render_template('auth/login.html', 
                                    msg={'status': 'error',
                                        'response': 'credenziali_errate', 
                                        'title': 'Credenziali non valide!',
                                        'message': 'La username o la password inserite non sono valide. Riprova.'
                                    })
        
        return render_template('auth/login.html')

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
        logout_user()
        # flash('Logout effettuato con successo')
        return render_template('auth/logout.html', logout=True)
        return redirect(url_for('web.index', logout=True))
    
    
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


