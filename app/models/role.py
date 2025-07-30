from app import db
from datetime import datetime

# Tabella di associazione many-to-many tra User e Role
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('assigned_at', db.DateTime, default=datetime.utcnow)
)

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relazione many-to-many con User
    users = db.relationship('User', secondary=user_roles, back_populates='roles')
    
    @classmethod
    def get_default_role(cls):
        """Restituisce il ruolo di default (user)"""
        return cls.query.filter_by(name='user').first()
    
    @classmethod
    def get_admin_role(cls):
        """Restituisce il ruolo admin"""
        return cls.query.filter_by(name='admin').first()
    
    @classmethod
    def create_default_roles(cls):
        """Crea i ruoli di default se non esistono"""
        default_roles = [
            {'name': 'superadmin', 'description': 'Amministratore con accesso globale'},
            {'name': 'admin', 'description': 'Amministratore'},
            {'name': 'user', 'description': 'Utente standard'},
            {'name': 'moderator', 'description': 'Moderatore con permessi limitati'},
            {'name': 'guest', 'description': 'Ospite con accesso di sola lettura'}
        ]
        
        for role_data in default_roles:
            existing_role = cls.query.filter_by(name=role_data['name']).first()
            if not existing_role:
                role = cls(
                    name=role_data['name'],
                    description=role_data['description']
                )
                db.session.add(role)
        
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Role {self.name}>'