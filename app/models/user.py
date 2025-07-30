from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func
import secrets
import os
import uuid
from app.utils.env_manager import *
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(255), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    profile_image = db.Column(db.String(255), nullable=True)  # Path dell'immagine
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=False)
    is_email_confirmed = db.Column(db.Boolean, default=False)
    email_confirmation_token = db.Column(db.String(255), nullable=True)
    email_confirmation_sent_at = db.Column(db.DateTime, nullable=True)
    password_reset_token = db.Column(db.String(255), nullable=True)
    password_reset_sent_at = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    qrcode_image = db.Column(db.String(255), nullable=True)
    qrcode_value = db.Column(db.String(255), nullable=True)
    company_uid = db.Column(db.String(255), db.ForeignKey('companies.uid'), nullable=True)

    # Relazione many-to-many con Role - specificando foreign_keys per evitare ambiguità
    roles = db.relationship('Role', 
                      secondary='user_roles', 
                      back_populates='users')
    
    # Relazione con Company
    company = db.relationship('Company', back_populates='users')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Aggiorna timestamp ultimo login"""
        self.last_login = datetime.utcnow()
    
    # ==================== NUOVE PROPRIETÀ PER I CAMPI AGGIUNTI ====================
    
    @property
    def full_name(self):
        """Restituisce nome completo"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username
    
    @property
    def initials(self):
        """Restituisce iniziali per avatar"""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        elif self.first_name:
            return self.first_name[0].upper()
        elif self.last_name:
            return self.last_name[0].upper()
        else:
            return self.username[0].upper() if self.username else "U"
    
    @property
    def avatar_url(self):
        """Restituisce URL dell'avatar (immagine o placeholder)"""
        if self.profile_image:
            # Controlla se il file esiste
            # static_path = f"app/static/{self.profile_image}"
            static_path = AVATAR_FOLDER
            if os.path.exists(static_path):
                return f"{AVATAR_URL}/{self.profile_image}"
        
        # Genera avatar con iniziali usando servizio esterno
        return f"https://ui-avatars.com/api/?name={self.initials}&background=30a257&color=fff&size=128"
    
    def set_profile_image(self, filename):
        """Imposta immagine profilo"""
        if filename:
            self.profile_image = f"uploads/avatars/{filename}"
        else:
            self.profile_image = None
    
    # ==================== GESTIONE RUOLI (ESISTENTE) ====================
    
    def add_role(self, role):
        """Aggiunge un ruolo all'utente"""
        if not self.has_role(role.name):
            self.roles.append(role)
    
    def remove_role(self, role):
        """Rimuove un ruolo dall'utente"""
        if self.has_role(role.name):
            self.roles.remove(role)
    
    def has_role(self, role_name):
        """Verifica se l'utente ha un ruolo specifico"""
        return any(role.name == role_name for role in self.roles)
    
    def has_any_role(self, role_names):
        """Verifica se l'utente ha almeno uno dei ruoli specificati"""
        return any(self.has_role(role_name) for role_name in role_names)
    
    def has_all_roles(self, role_names):
        """Verifica se l'utente ha tutti i ruoli specificati"""
        return all(self.has_role(role_name) for role_name in role_names)
    
    def is_admin(self):
        """Verifica se l'utente è admin"""
        return self.has_role('admin')
    
    def is_moderator(self):
        """Verifica se l'utente è moderator"""
        return self.has_role('moderator')
    
    def can_manage_users(self):
        """Verifica se può gestire utenti"""
        return self.has_any_role(['admin', 'moderator'])
    
    def get_role_names(self):
        """Restituisce lista nomi ruoli"""
        return [role.name for role in self.roles]
    
    def get_highest_role(self):
        """Restituisce il ruolo più alto (in ordine di priorità)"""
        role_priority = {'admin': 1, 'moderator': 2, 'user': 3, 'guest': 4}
        user_roles = [role.name for role in self.roles]
        
        if not user_roles:
            return None
        
        # Ordina per priorità e restituisce il primo
        sorted_roles = sorted(user_roles, key=lambda x: role_priority.get(x, 999))
        return sorted_roles[0]
    
    def assign_default_role(self):
        """Assegna il ruolo di default (user) se non ha ruoli"""
        if not self.roles:
            # Import lazy per evitare circular import
            from app.models.role import Role
            default_role = Role.get_default_role()
            if default_role:
                self.add_role(default_role)
    
    # ==================== TOKEN METHODS (ESISTENTI) ====================
    
    def generate_confirmation_token(self):
        """Genera token di conferma email"""
        self.email_confirmation_token = secrets.token_urlsafe(32)
        self.email_confirmation_sent_at = datetime.utcnow()
        return self.email_confirmation_token
    
    def is_confirmation_token_valid(self, token, max_age_hours=24):
        """Verifica se il token di conferma è valido"""
        if not self.email_confirmation_token or not self.email_confirmation_sent_at:
            return False
        
        if self.email_confirmation_token != token:
            return False
        
        expiry_time = self.email_confirmation_sent_at + timedelta(hours=max_age_hours)
        return datetime.utcnow() <= expiry_time
    
    def confirm_email(self, token):
        """Conferma l'email con il token"""
        if self.is_confirmation_token_valid(token):
            self.is_email_confirmed = True
            self.email_confirmation_token = None
            self.email_confirmation_sent_at = None
            return True
        return False
    
    def generate_password_reset_token(self):
        """Genera token per reset password"""
        self.password_reset_token = secrets.token_urlsafe(32)
        self.password_reset_sent_at = datetime.utcnow()
        return self.password_reset_token
    
    def is_password_reset_token_valid(self, token, max_age_hours=1):
        """Verifica se il token di reset password è valido"""
        if not self.password_reset_token or not self.password_reset_sent_at:
            return False
        
        if self.password_reset_token != token:
            return False
        
        expiry_time = self.password_reset_sent_at + timedelta(hours=max_age_hours)
        return datetime.utcnow() <= expiry_time
    
    def reset_password(self, token, new_password):
        """Reset password con token"""
        if self.is_password_reset_token_valid(token):
            self.set_password(new_password)
            self.password_reset_token = None
            self.password_reset_sent_at = None
            return True
        return False
    
    # ==================== QUERY METHODS (ESISTENTI + NUOVI) ====================
    
    @classmethod
    def find_by_email_login(cls, email):
        """Trova utente per email nel login (case-insensitive)"""
        return cls.query.filter(func.lower(cls.email) == func.lower(email)).first()
    
    @classmethod
    def find_by_username(cls, username):
        """Trova utente per username (case-insensitive)"""
        return cls.query.filter(func.lower(cls.username) == func.lower(username)).first()
    
    @classmethod
    def find_by_email(cls, email):
        """Trova utente per email (case-insensitive)"""
        return cls.query.filter(func.lower(cls.email) == func.lower(email)).first()
    
    @classmethod
    def find_by_phone(cls, phone):
        """Trova utente per telefono"""
        return cls.query.filter_by(phone=phone).first()
    
    @classmethod
    def find_by_confirmation_token(cls, token):
        """Trova utente per token di conferma"""
        return cls.query.filter_by(email_confirmation_token=token).first()
    
    @classmethod
    def find_by_password_reset_token(cls, token):
        """Trova utente per token di reset password"""
        return cls.query.filter_by(password_reset_token=token).first()
    
    @classmethod
    def get_users_by_role(cls, role_name):
        """Restituisce tutti gli utenti con un ruolo specifico"""
        from app.models.role import Role
        role = Role.query.filter_by(name=role_name).first()
        if role:
            return role.users
        return []
    
    @classmethod
    def get_admins(cls):
        """Restituisce tutti gli admin"""
        return cls.get_users_by_role('admin')
    
    @classmethod
    def find_by_uid(cls, uid):
        """Trova utente per UID"""
        return cls.query.filter_by(uid=uid).first()
    
    @classmethod
    def get_by_uid(cls, uid):
        """Ottiene utente per UID (con eccezione se non trovato)"""
        return cls.query.filter_by(uid=uid).first_or_404()

    @classmethod
    def find_by_id(cls, id):
        """Trova utente per ID"""
        return cls.query.filter_by(id=id).first()
    
    @classmethod
    def find_by_uid_or_id(cls, identifier):
        """Trova utente per UID o ID"""
        # Prova prima con UID
        user = cls.query.filter_by(uid=identifier).first()
        if not user:
            # Prova con ID se è un numero
            try:
                user_uid = int(identifier)
                user = cls.query.filter_by(id=user_uid).first()
            except ValueError:
                pass
        return user
    
    # ==================== SERIALIZZAZIONE AGGIORNATA ====================
    
    def to_dict(self, include_roles=True, include_sensitive=False):
        """Converte utente in dizionario con campi aggiornati"""
        data = {
            'id': self.id,
            'uid': self.uid,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'phone': self.phone,
            'profile_image': self.profile_image,
            'avatar_url': self.avatar_url,
            'initials': self.initials,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'is_email_confirmed': self.is_email_confirmed,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'qrcode_image': self.qrcode_image,
            'qrcode_value': self.qrcode_value,
            'company_uid': self.company_uid,
            'company_name': self.company.nome_societa if self.company else None,
        }
        
        if include_roles:
            data['roles'] = [role.to_dict() for role in self.roles]
            data['role_names'] = self.get_role_names()
            data['highest_role'] = self.get_highest_role()
            data['is_admin'] = self.is_admin()
            data['is_moderator'] = self.is_moderator()
            data['can_manage_users'] = self.can_manage_users()
        
        if include_sensitive:
            data['email_confirmation_token'] = self.email_confirmation_token
            data['password_reset_token'] = self.password_reset_token
            data['email_confirmation_sent_at'] = self.email_confirmation_sent_at.isoformat() if self.email_confirmation_sent_at else None
            data['password_reset_sent_at'] = self.password_reset_sent_at.isoformat() if self.password_reset_sent_at else None
        
        return data
    
    def __repr__(self):
        roles = ', '.join(self.get_role_names())
        full_name = f" ({self.full_name})" if self.full_name != self.username else ""
        return f'<User {self.username}{full_name} - {self.email} - Roles: {roles}>'
    

    @staticmethod
    def generate_uid():
        """Genera un UID univoco per l'utente"""
        import uuid
        return str(uuid.uuid4())

    def __init__(self, **kwargs):
        """Inizializza l'utente con UID automatico"""
        super().__init__(**kwargs)
        if not self.uid:
            self.uid = self.generate_uid()


    #"""Genera un QR code per l'utente"""
    def generate_qr_code(self, value=None):
        import qrcode
        import io
        import base64
        from PIL import Image
        
        if not value:
            value = self.uid
        
        # Genera QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(value)
        qr.make(fit=True)
        
        # Crea l'immagine
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Converti in base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        # Salva nel database
        self.qrcode_value = value
        self.qrcode_image = f"data:image/png;base64,{img_str}"
        
        return self.qrcode_image

    def get_qr_code_image_path(self):
        """Ritorna il path dell'immagine QR code"""
        return self.qrcode_image

    @property
    def qr_code_data(self):
        """Restituisce i dati del QR code"""
        return {
            'value': self.qrcode_value,
            'image': self.qrcode_image
        }
    

    ##Gestisce i gruppi
    def add_to_group(self, group_name):
        """Aggiunge l'utente a un gruppo"""
        if not self.groups:
            self.groups = group_name
        else:
            groups_list = self.groups.split(',')
            if group_name not in groups_list:
                groups_list.append(group_name)
                self.groups = ','.join(groups_list)

    def remove_from_group(self, group_name):
        """Rimuove l'utente da un gruppo"""
        if self.groups:
            groups_list = self.groups.split(',')
            if group_name in groups_list:
                groups_list.remove(group_name)
                self.groups = ','.join(groups_list) if groups_list else None

    def get_groups_list(self):
        """Restituisce la lista dei gruppi"""
        return self.groups.split(',') if self.groups else []

    def is_in_group(self, group_name):
        """Controlla se l'utente appartiene a un gruppo"""
        return group_name in self.get_groups_list()