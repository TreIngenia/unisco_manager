import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import url_for, current_app
import os

class EmailService:
    
    @staticmethod
    def send_confirmation_email(user_email, username, confirmation_token):
        """Invia email di conferma registrazione"""
        try:
            # Configurazione SMTP
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', '587'))
            sender_email = os.environ.get('SENDER_EMAIL')
            sender_password = os.environ.get('SENDER_PASSWORD')
            sender_name = os.environ.get('SENDER_NAME')
            sende_cc = os.environ.get('SENDEER_CC')

            if not sender_email or not sender_password:
                print("⚠️ Configurazione email mancante - simulazione invio email")
                return EmailService._simulate_email_send(user_email, username, confirmation_token)
            
            # Creazione del messaggio
            message = MIMEMultipart("alternative")
            message["Subject"] = "Conferma la tua registrazione"
            message["From"] = sender_email
            message["To"] = user_email
            
            # URL di conferma
            confirmation_url = url_for('auth.confirm_email', 
                                     token=confirmation_token, 
                                     _external=True)
            
            logo_url = url_for('static', filename='assets/media/logos/unisco_orizzontale.svg', _external=True)
            # Corpo dell'email in HTML
            html_body = f"""
                <div style="font-family:Arial,Helvetica,sans-serif; line-height: 1.5; font-weight: normal; font-size: 15px; color: #2F3044; min-height: 100%; margin:0; padding:0; width:100%; background-color:#edf2f7">
                    <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="border-collapse:collapse;margin:0 auto; padding:0; max-width:600px">
                        <tbody>
                            <tr>
                                <td align="center" valign="center" style="text-align:center; padding: 40px">
                                    <a href="https://unisco.pro" rel="noopener" target="_blank">
                                        <img alt="Logo" src="{logo_url}" />
                                    </a>
                                </td>
                            </tr>
                            <tr>
                                <td align="left" valign="center">
                                    <div style="text-align:left; margin: 0 20px; padding: 40px; background-color:#ffffff; border-radius: 6px">
                                        <!--begin:Email content-->
                                        <div style="padding-bottom: 30px; font-size: 17px;">
                                            <strong>Benvenuto <br>{username}!</strong>
                                        </div>
                                        <div style="padding-bottom: 30px">Grazie per esserti registrato alla nostra applicazione. Per completare la registrazione, clicca sul pulsante qui sotto</div>
                                        <div style="padding-bottom: 40px; text-align:center;">
                                            <a href="{confirmation_url}" rel="noopener" style="text-decoration:none;display:inline-block;text-align:center;padding:0.75575rem 1.3rem;font-size:0.925rem;line-height:1.5;border-radius:0.35rem;color:#ffffff;background-color:#4CAF50;border:0px;margin-right:0.75rem!important;font-weight:600!important;outline:none!important;vertical-align:middle" target="_blank">Conferma Email</a>
                                        </div>
                                        <div style="padding-bottom: 30px">Questo link di conferma è valido per 24 ore, una volta scaduto si dovrà procedere a richiederne uno nuovo, provando ad effettuare il login.</div>
                                        <div style="border-bottom: 1px solid #eeeeee; margin: 15px 0"></div>
                                        <div style="padding-bottom: 50px; word-wrap: break-all;">
                                            <p style="margin-bottom: 10px;">Se il pulsante non funziona, copia e incolla questo link nel tuo browser:</p>
                                            <a href="{confirmation_url}" rel="noopener" target="_blank" style="text-decoration:none;color: #009ef7">{confirmation_url}</a>
                                        </div>
                                        <!--end:Email content-->
                                        <div style="padding-bottom: 10px">Grazie,
                                        <br>Il team Unisco. 
                                        <tr>
                                            <td align="center" valign="center" style="font-size: 13px; text-align:center;padding: 20px; color: #6d6e7c;">
                                                <p>Unisco by Treingenia srl | Via Cornelia, 498 (blocco 4) | 00166 Roma</p>
                                                <p>Copyright &copy; 
                                                <a href="https://unisco.pro" rel="noopener" target="_blank">Unisco</a></p>
                                            </td>
                                        </tr></br></div>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            """

            # Corpo dell'email in testo semplice
            text_body = f"""
            Benvenuto {username}!
            
            Grazie per esserti registrato alla nostra applicazione.
            
            Per completare la registrazione, visita questo link:
            {confirmation_url}
            
            Questo link è valido per 24 ore.
            
            Se non hai richiesto questa registrazione, ignora questa email.
            """
            
            # Aggiungi entrambe le versioni
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Invio dell'email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
            
            print(f"✅ Email di conferma inviata a {user_email}")
            return True
            
        except Exception as e:
            print(f"❌ Errore invio email: {e}")
            # In caso di errore, simula l'invio per sviluppo
            return EmailService._simulate_email_send(user_email, username, confirmation_token)
        

    @staticmethod
    def send_password_reset_email(user_email, username, reset_token):
        """Invia email per reset password"""
        try:
            # Configurazione SMTP
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', '587'))
            sender_email = os.environ.get('SENDER_EMAIL')
            sender_password = os.environ.get('SENDER_PASSWORD')
            
            if not sender_email or not sender_password:
                print("⚠️ Configurazione email mancante - simulazione invio email")
                return EmailService._simulate_password_reset_email(user_email, username, reset_token)
            
            # Creazione del messaggio
            message = MIMEMultipart("alternative")
            message["Subject"] = "Reset della tua password"
            message["From"] = sender_email
            message["To"] = user_email
            
            # URL di reset
            reset_url = url_for('auth.reset_password', 
                               token=reset_token, 
                               _external=True)
            
            # Corpo dell'email in HTML
            html_body = f"""
            <html>
                <body>
                    <h2>Reset Password</h2>
                    <p>Ciao {username},</p>
                    <p>Hai richiesto il reset della tua password.</p>
                    <p>Per reimpostare la password, clicca sul link qui sotto:</p>
                    <p>
                        <a href="{reset_url}" 
                           style="background-color: #FF6B6B; color: white; padding: 10px 20px; 
                                  text-decoration: none; border-radius: 5px;">
                            Reset Password
                        </a>
                    </p>
                    <p>Se il pulsante non funziona, copia e incolla questo link nel tuo browser:</p>
                    <p>{reset_url}</p>
                    <p><small><strong>Importante:</strong> Questo link è valido solo per 1 ora per motivi di sicurezza.</small></p>
                    <hr>
                    <p><small>Se non hai richiesto questo reset, ignora questa email. La tua password rimarrà invariata.</small></p>
                </body>
            </html>
            """
            
            # Corpo dell'email in testo semplice
            text_body = f"""
            Reset Password
            
            Ciao {username},
            
            Hai richiesto il reset della tua password.
            
            Per reimpostare la password, visita questo link:
            {reset_url}
            
            IMPORTANTE: Questo link è valido solo per 1 ora per motivi di sicurezza.
            
            Se non hai richiesto questo reset, ignora questa email.
            """
            
            # Aggiungi entrambe le versioni
            text_part = MIMEText(text_body, "plain")
            html_part = MIMEText(html_body, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Invio dell'email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
            
            print(f"✅ Email di reset password inviata a {user_email}")
            return True
            
        except Exception as e:
            print(f"❌ Errore invio email: {e}")
            # In caso di errore, simula l'invio per sviluppo
            return EmailService._simulate_password_reset_email(user_email, username, reset_token)
        
        
    @staticmethod
    def _simulate_email_send(user_email, username, confirmation_token):
        """Simula l'invio email per sviluppo"""
        confirmation_url = url_for('auth.confirm_email', 
                                 token=confirmation_token, 
                                 _external=True)
        
        print("\n" + "="*60)
        print("📧 SIMULAZIONE INVIO EMAIL DI CONFERMA")
        print("="*60)
        print(f"A: {user_email}")
        print(f"Oggetto: Conferma la tua registrazione")
        print("-"*60)
        print(f"Ciao {username}!")
        print("")
        print("Per completare la registrazione, visita questo link:")
        print(f"{confirmation_url}")
        print("")
        print("Link valido per 24 ore.")
        print("="*60)
        print("✅ Email simulata - controlla la console per il link!\n")
        
        return True
    
    
    @staticmethod
    def _simulate_password_reset_email(user_email, username, reset_token):
        """Simula l'invio email di reset password per sviluppo"""
        reset_url = url_for('auth.reset_password', 
                           token=reset_token, 
                           _external=True)
        
        print("\n" + "="*60)
        print("🔑 SIMULAZIONE INVIO EMAIL RESET PASSWORD")
        print("="*60)
        print(f"A: {user_email}")
        print(f"Oggetto: Reset della tua password")
        print("-"*60)
        print(f"Ciao {username}!")
        print("")
        print("Per reimpostare la password, visita questo link:")
        print(f"{reset_url}")
        print("")
        print("⚠️ Link valido per 1 ora!")
        print("="*60)
        print("✅ Email simulata - controlla la console per il link!\n")
        
        return True